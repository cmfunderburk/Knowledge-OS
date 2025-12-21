"""
CLI dashboard - shows today's study plan.

Displays domain, reviewer status, reader status, and next task.
"""
import datetime

# ANSI Colors
BOLD = '\033[1m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
CYAN = '\033[36m'
DIM = '\033[2m'
RESET = '\033[0m'


def run_today() -> None:
    """Print CLI dashboard."""
    from knos.reviewer.core import (
        get_todays_domain,
        get_next_task,
        get_reviewer_summary,
        get_overall_progress,
        collect_focus_files,
    )
    from reader.config import load_registry
    from reader.session import list_sessions, SESSIONS_DIR

    _print_header()
    _print_domain(get_todays_domain())
    _print_reviewer_status(get_reviewer_summary)
    _print_reader_status(load_registry, list_sessions, SESSIONS_DIR)
    _print_card_summary(collect_focus_files())
    _print_next_task(get_overall_progress(), get_next_task())
    _print_quick_commands()


def _print_header() -> None:
    date_str = datetime.date.today().strftime("%A, %B %d, %Y")
    print(f"{BOLD}╔════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}║           TODAY'S STUDY PLAN           ║{RESET}")
    print(f"{BOLD}║  {CYAN}{date_str:<26}{RESET}{BOLD}     ║{RESET}")
    print(f"{BOLD}╚════════════════════════════════════════╝{RESET}")
    print()


def _print_domain(domain_info: tuple[str, str | None]) -> None:
    domain, override = domain_info
    if override:
        print(f"{BOLD}Current Phase:{RESET} {YELLOW}{domain}{RESET}")
        print(f"{DIM}{override}{RESET}")
    else:
        print(f"{BOLD}Domain:{RESET} {GREEN}{domain}{RESET}")
    print()


def _print_reviewer_status(get_reviewer_summary_fn) -> None:
    """Print reviewer status. Takes callable to handle exceptions gracefully."""
    print(f"{BOLD}Reviewer:{RESET}")
    try:
        summary = get_reviewer_summary_fn()
        box_zero = summary["box_zero"]
        overdue = summary["overdue"]
        due_now = summary["due_now"]
        never_practiced = summary["never_practiced"]
        total_due = box_zero + overdue + due_now

        if box_zero > 0:
            print(f"  {YELLOW}Box 0 (failed): {box_zero} cards{RESET}")
        if overdue > 0:
            print(f"  {YELLOW}Overdue: {overdue} cards{RESET}")
        if due_now > 0:
            print(f"  {GREEN}Due now: {due_now} cards{RESET}")
        if total_due == 0:
            print(f"  {GREEN}All caught up!{RESET}")
        if never_practiced > 0:
            print(f"  {DIM}Never practiced: {never_practiced} cards{RESET}")

        if summary["last_practiced"]:
            last_date = summary["last_practiced"][:10]
            print(f"  {DIM}Last practiced: {last_date}{RESET}")
    except Exception as e:
        print(f"  {DIM}(error reading reviewer data: {e}){RESET}")
    print()


def _print_reader_status(load_registry_fn, list_sessions_fn, sessions_dir) -> None:
    """Print reader status. Takes callables to handle exceptions gracefully."""
    print(f"{BOLD}Reader:{RESET}")
    try:
        registry = load_registry_fn()
        materials = registry.get("materials", {})
        material_count = len(materials)

        all_sessions = []
        if sessions_dir.exists():
            for material_dir in sessions_dir.iterdir():
                if material_dir.is_dir():
                    material_id = material_dir.name
                    sessions = list_sessions_fn(material_id)
                    for chapter_num, session in sessions.items():
                        material_info = materials.get(material_id, {})
                        title = material_info.get("title", material_id)
                        all_sessions.append((session, title))

        if not all_sessions:
            print(f"  {DIM}No reading sessions yet{RESET}")
            print(f"  {DIM}Materials: {material_count} registered{RESET}")
        else:
            all_sessions.sort(key=lambda x: x[0].last_updated, reverse=True)
            last_session, last_title = all_sessions[0]

            now = datetime.datetime.now()
            delta = now - last_session.last_updated
            if delta.days == 0:
                time_ago = "today"
            elif delta.days == 1:
                time_ago = "yesterday"
            else:
                time_ago = f"{delta.days} days ago"

            display_title = last_title if len(last_title) <= 30 else last_title[:27] + "..."
            print(f"  Last session: {display_title}, Ch {last_session.chapter_num} ({time_ago})")
            print(f"  {DIM}In progress: {len(all_sessions)} chapter(s) · Materials: {material_count}{RESET}")
    except Exception as e:
        print(f"  {DIM}(error reading reader data: {e}){RESET}")
    print()


def _print_card_summary(focus_files: list) -> None:
    count = len(focus_files)
    if count > 0:
        print(f"{BOLD}Reviewer Library:{RESET}")
        print(f"  {DIM}Focus cards: {count}{RESET}")
        print()


def _print_next_task(progress: tuple[int, int], next_task: str | None) -> None:
    done, total = progress
    if total == 0:
        return

    print(f"{BOLD}Phase 0 Progress:{RESET} {done}/{total} tasks complete")
    if next_task:
        print(f"  {CYAN}Next:{RESET}  {next_task}")
    else:
        print(f"  {GREEN}All Phase 0 tasks complete!{RESET}")
    print()


def _print_quick_commands() -> None:
    print(f"{BOLD}Quick Commands:{RESET}")
    print(f"  {GREEN}knos{RESET}                     # Launch TUI (recommended)")
    print(f"  {GREEN}knos drill{RESET}               # Drill due cards")
    print(f"  {GREEN}knos read{RESET}                # Reading companion")
    print(f"  {DIM}knos progress{RESET}            # Generate progress report")
    print()
