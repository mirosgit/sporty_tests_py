"""Shared fixtures, BDD steps, failure diagnostics and the end-of-run test report."""

from __future__ import annotations

import datetime as dt
import logging
import re
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver

from config.settings import Settings
from src.api.api_client import ApiClient
from src.api.betting_api import BettingApi
from src.pages.bet_slip import BetSlip
from src.pages.header import Header
from src.pages.match_list_page import MatchListPage
from src.pages.receipt_modal import ReceiptModal

logger = logging.getLogger(__name__)

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "artifacts" / "screenshots"
WINDOW_SIZE = "1920,1080"

# Per-test data for the failure hook and the test report.
DRIVER_KEY = pytest.StashKey[WebDriver]()
SCENARIO_KEY = pytest.StashKey[str]()
FAILED_STEP_KEY = pytest.StashKey[str]()
RUN_ORDER_KEY = pytest.StashKey[dict[str, int]]()


# --- Configuration and API ---------------------------------------------------


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings.from_env()


@pytest.fixture(scope="session")
def api_client(settings: Settings) -> Iterator[ApiClient]:
    client = ApiClient(settings.api_url, settings.user_id, settings.default_timeout)
    yield client
    client.close()


@pytest.fixture(scope="session")
def betting_api(api_client: ApiClient) -> BettingApi:
    return BettingApi(api_client)


# --- Test state and data ------------------------------------------------------


@pytest.fixture
def start_balance(betting_api: BettingApi) -> Decimal:
    """Reset the account balance, so each test starts from the same known state."""
    return betting_api.reset_balance()


@pytest.fixture(scope="session")
def upcoming_match(betting_api: BettingApi) -> dict[str, Any]:
    """The nearest match with a kickoff date after today, from the live catalog."""
    today = dt.date.today().isoformat()
    upcoming = [match for match in betting_api.get_matches() if match["kickoffDate"] > today]
    if not upcoming:
        pytest.skip("The match catalog has no upcoming matches")
    return min(upcoming, key=lambda match: match["kickoffDate"])


# --- Browser and page objects -------------------------------------------------


@pytest.fixture
def driver(request: pytest.FixtureRequest, settings: Settings) -> Iterator[WebDriver]:
    options = webdriver.ChromeOptions()
    if settings.headless:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={WINDOW_SIZE}")
    try:
        chrome = webdriver.Chrome(options=options)
    except WebDriverException as error:
        raise RuntimeError(
            f"Could not start Chrome. Is Google Chrome installed? {error.msg}"
        ) from error
    request.node.stash[DRIVER_KEY] = chrome
    try:
        yield chrome
    finally:
        # A failed quit must not hide the test result.
        try:
            chrome.quit()
        except WebDriverException as error:
            logger.warning("Could not close Chrome: %s", error.msg)


@pytest.fixture
def match_list_page(driver: WebDriver, settings: Settings, start_balance: Decimal) -> MatchListPage:
    """Open the app after the balance reset, so the page shows the starting balance."""
    return MatchListPage(driver, settings.default_timeout).open(settings.app_url)


@pytest.fixture
def header(driver: WebDriver, settings: Settings) -> Header:
    return Header(driver, settings.default_timeout)


@pytest.fixture
def bet_slip(driver: WebDriver, settings: Settings) -> BetSlip:
    return BetSlip(driver, settings.default_timeout)


@pytest.fixture
def receipt_modal(driver: WebDriver, settings: Settings) -> ReceiptModal:
    return ReceiptModal(driver, settings.default_timeout)


# --- Shared BDD steps ---------------------------------------------------------


@given("the balance is reset")
def balance_is_reset(start_balance: Decimal) -> None:
    """The start_balance fixture resets the balance."""


# --- Failure diagnostics and test report -------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    # pytest-bdd does not create the folder for its JSON report.
    for path in (config.option.xmlpath, config.option.cucumber_json_path):
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    config.stash[RUN_ORDER_KEY] = {item.nodeid: index for index, item in enumerate(items)}


def pytest_bdd_before_scenario(request: pytest.FixtureRequest, scenario: Any) -> None:
    request.node.stash[SCENARIO_KEY] = scenario.name


def pytest_bdd_step_error(request: pytest.FixtureRequest, step: Any) -> None:
    request.node.stash[FAILED_STEP_KEY] = f"{step.keyword} {step.name}"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item) -> Iterator[None]:
    """Attach the scenario, the failed step and a screenshot to the test report."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    for key, name in ((SCENARIO_KEY, "scenario"), (FAILED_STEP_KEY, "failed_step")):
        if key in item.stash:
            report.user_properties.append((name, item.stash[key]))
    known_defect = report.skipped and hasattr(report, "wasxfail")
    if (report.failed or known_defect) and (screenshot := _save_screenshot(item)):
        report.user_properties.append(("screenshot", str(screenshot)))
        report.sections.append(("screenshot", str(screenshot)))


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter, config: pytest.Config
) -> None:
    """Print one line per test, with the failed step, the reason and the screenshot."""
    reports = [
        report
        for status in ("passed", "failed", "error", "skipped", "xfailed", "xpassed")
        for report in terminalreporter.stats.get(status, [])
        if isinstance(report, pytest.TestReport)
        and (report.when == "call" or report.outcome != "passed")
    ]
    if not reports:
        return
    run_order = config.stash.get(RUN_ORDER_KEY, {})
    reports.sort(key=lambda report: run_order.get(report.nodeid, len(run_order)))

    write = terminalreporter.write_line
    terminalreporter.write_sep("=", "Test report")
    for report in reports:
        details = dict(report.user_properties)
        result = _result(report)
        name = details.get("scenario", report.head_line or report.nodeid)
        write(f"{result:<7} {name}{_test_parameters(report.nodeid)}", **_COLOURS[result])
        if report.failed or report.skipped:
            if "failed_step" in details:
                write(f"        step:       {details['failed_step']}")
            first_line, *other_lines = _failure_reason(report)
            write(f"        reason:     {first_line}")
            for line in other_lines:
                write(f"                    {line}")
            if "screenshot" in details:
                write(f"        screenshot: {_relative(details['screenshot'], config)}")
    report_files = [config.option.xmlpath, config.option.cucumber_json_path]
    if any(report_files):
        write(f"Report files: {', '.join(path for path in report_files if path)}")


_COLOURS = {
    "PASSED": {"green": True},
    "FAILED": {"red": True},
    "ERROR": {"red": True},
    "SKIPPED": {"yellow": True},
    "XFAIL": {"yellow": True},
    "XPASS": {"red": True},
}


def _result(report: pytest.TestReport) -> str:
    """PASSED, FAILED, ERROR, SKIPPED, or XFAIL / XPASS for tests tagged @xfail."""
    if hasattr(report, "wasxfail"):
        return "XFAIL" if report.skipped else "XPASS"
    if report.failed and report.when != "call":
        return "ERROR"
    return report.outcome.upper()


def _test_parameters(nodeid: str) -> str:
    """The example values of a scenario outline, e.g. ' [-5-invalid_stake_min]'."""
    return f" [{nodeid.split('[', 1)[1]}" if "[" in nodeid else ""


def _relative(path: str, config: pytest.Config) -> str:
    try:
        return str(Path(path).relative_to(config.rootpath))
    except ValueError:
        return path


def _failure_reason(report: pytest.TestReport) -> list[str]:
    """The failure message in full, without pytest's 'assert ...' introspection."""
    if isinstance(report.longrepr, tuple):  # a skip: (path, line, reason)
        return [report.longrepr[2]]
    crash = getattr(report.longrepr, "reprcrash", None)
    text = crash.message if crash else str(report.longrepr)
    if text.startswith("[XPASS(strict)]"):
        return ["passed although tagged @xfail: the known defect looks fixed, remove the tag"]
    first_line, *other_lines = text.removeprefix("AssertionError: ").splitlines() or [""]
    message = [first_line]
    for line in other_lines:
        if line.startswith("assert "):
            break
        message.append(line.strip())
    return message


def _save_screenshot(item: pytest.Item) -> Path | None:
    """Save a screenshot of the test's browser, if it has one. Never raises."""
    driver = item.stash.get(DRIVER_KEY, None)
    if driver is None:
        return None
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    test_name = re.sub(r"[^\w.-]", "_", item.name)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = SCREENSHOTS_DIR / f"{test_name}_{timestamp}.png"
    # Diagnostics must never break the run, e.g. when the browser has already crashed.
    try:
        saved = driver.save_screenshot(str(path))
    except WebDriverException as error:
        logger.warning("Could not save a screenshot: %s", error.msg)
        return None
    if not saved:
        logger.warning("Could not save a screenshot to %s", path)
        return None
    logger.error("Screenshot saved: %s", path)
    return path
