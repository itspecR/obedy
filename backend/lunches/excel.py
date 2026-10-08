from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from accounts.names import display_name
from lunches.clock import clock_text, local
from lunches.statistics import SECONDS_IN_MINUTE
from lunches.status import MEASURED, duration_of, is_violation, status_of

PEOPLE_SHEET = "Сотрудники"
LUNCHES_SHEET = "Все обеды"
PEOPLE_HEADERS = ["Сотрудник", "Логин", "Обедов", "Нарушений", "Превышений", "Без возврата", "Среднее, мин", "Перебор, мин"]
LUNCH_HEADERS = ["Дата", "Сотрудник", "Логин", "Ушёл", "Вернулся", "Длительность, мин", "Лимит, мин", "Статус", "Изменение", "Кто изменил", "Причина"]
ADDED = "Добавлено"
CORRECTED = "Исправлено"
FORMULA_TYPE = "f"
TEXT_TYPE = "s"
DATE_FORMAT = "DD.MM.YYYY"
DATE_COLUMN = 1
HEADER_FONT = Font(bold=True)
ALARM_FILL = PatternFill("solid", fgColor="FDE2E1")
MIN_WIDTH = 8
MAX_WIDTH = 60
WIDTH_PADDING = 2


def person_row(stats):
    account = stats.account
    return [
        display_name(account),
        account.login,
        stats.count,
        stats.violations,
        stats.overruns,
        stats.unreturned,
        stats.average_minutes,
        stats.overrun_minutes,
    ]


def change_of(lunch):
    if lunch.corrected_at is None:
        return ["", "", ""]
    author = display_name(lunch.corrected_by) if lunch.corrected_by else ""
    return [ADDED if lunch.added_by_hand else CORRECTED, author, lunch.correction_reason]


def lunch_row(lunch, now):
    status = status_of(lunch, now)
    duration = round(duration_of(lunch, now).total_seconds() / SECONDS_IN_MINUTE) if status in MEASURED else None
    return [
        lunch.day,
        display_name(lunch.account),
        lunch.account.login,
        clock_text(local(lunch.started_at)),
        clock_text(local(lunch.ended_at)) if lunch.ended_at else "",
        duration,
        lunch.limit_minutes,
        status.label,
        *change_of(lunch),
    ]


def fit_columns(sheet):
    for index, column in enumerate(sheet.iter_cols(values_only=True), start=1):
        longest = max(len(str(value)) for value in column if value is not None)
        sheet.column_dimensions[get_column_letter(index)].width = min(MAX_WIDTH, max(MIN_WIDTH, longest + WIDTH_PADDING))


def keep_as_text(cell):
    if cell.data_type == FORMULA_TYPE:
        cell.data_type = TEXT_TYPE


def fill_sheet(sheet, headers, rows):
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = HEADER_FONT
    for values, alarming in rows:
        sheet.append(values)
        for cell in sheet[sheet.max_row]:
            keep_as_text(cell)
            if alarming:
                cell.fill = ALARM_FILL
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    fit_columns(sheet)


def format_dates(sheet):
    for row in sheet.iter_rows(min_row=2, min_col=DATE_COLUMN, max_col=DATE_COLUMN):
        row[0].number_format = DATE_FORMAT


def workbook_bytes(people, lunches, now):
    book = Workbook()
    people_sheet = book.active
    people_sheet.title = PEOPLE_SHEET
    fill_sheet(people_sheet, PEOPLE_HEADERS, [(person_row(stats), stats.violations > 0) for stats in people])
    lunches_sheet = book.create_sheet(LUNCHES_SHEET)
    fill_sheet(lunches_sheet, LUNCH_HEADERS, [(lunch_row(lunch, now), is_violation(lunch, now)) for lunch in lunches])
    format_dates(lunches_sheet)
    buffer = BytesIO()
    book.save(buffer)
    return buffer.getvalue()
