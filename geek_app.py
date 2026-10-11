
"""GEEK Control - ESP32-S3-GEEK / MicroPython."""

import os
import gc
import display
import draw
import write

BLACK = 0x0000
WHITE = 0xFFFF
CYAN = 0x07FF
GREEN = 0x07E0
YELLOW = 0xFFE0
RED = 0xF800
GRAY = 0x8410

PAGE_SIZE = 6


def label(x, y, value, color=WHITE, size=8):
    write.text(x, y, str(value), color, BLACK, size)


def screen(title, subtitle=""):
    display.fill_screen(BLACK)
    label(4, 3, str(title)[:29], CYAN)

    if subtitle:
        label(4, 17, str(subtitle)[:29], GRAY)

    draw.line(2, 29, display.WIDTH - 3, 29, CYAN)


def message(title, lines):
    screen(title)

    for i, line in enumerate(lines[:9]):
        label(4, 33 + i * 11, str(line)[:29])


def short_name(name, length=22):
    if len(name) <= length:
        return name
    return name[:length - 2] + ".."


def show_listing(items, page, selected=None):
    count = len(items)
    pages = max(1, (count + PAGE_SIZE - 1) // PAGE_SIZE)

    screen(
        "SD FILE MANAGER",
        "%d files | page %d/%d" % (count, page + 1, pages)
    )

    start = page * PAGE_SIZE
    end = min(count, start + PAGE_SIZE)

    for row, idx in enumerate(range(start, end)):
        color = YELLOW if idx == selected else WHITE
        name = short_name(items[idx], 23)

        label(
            4,
            35 + row * 14,
            "%d %s" % (idx + 1, name),
            color
        )

    label(4, 122, "N next P prev / # select", GREEN)


def show_file(sd, name):
    """Lee solamente una vista previa del archivo."""

    path = sd._path(name)

    with open(path, "rb") as f:
        sample = f.read(512)

    # Los archivos binarios no se interpretan como texto.
    if b"\x00" in sample:
        print("Binary file:", name)
        print(repr(sample[:64]))

        message(
            "BINARY FILE",
            [
                short_name(name, 28),
                "Preview in REPL",
                repr(sample[:12])
            ]
        )
        return

    try:
        content = sample.decode("utf-8")
    except UnicodeError:
        content = "".join(
            chr(c) if 32 <= c <= 126 else "."
            for c in sample
        )

    print("File:", name)
    print(repr(content))

    if len(sample) == 512:
        print("Preview limited to first 512 bytes")

    # Dividir en lineas de hasta 29 caracteres.
    lines = []

    for logical_line in content.replace("\r", "").split("\n"):
        while len(logical_line) > 29:
            lines.append(logical_line[:29])
            logical_line = logical_line[29:]

        lines.append(logical_line)

    message(
        "READ: " + short_name(name, 23),
        lines
    )

    if len(lines) > 9:
        print("Only first 9 lines fit the display")


def ask_file_number(prompt, count):
    value = input(prompt).strip()

    if not value.isdigit():
        return None

    index = int(value) - 1

    if 0 <= index < count:
        return index

    return None


def sd_menu():
    from sd_files import SDStorage

    sd = SDStorage().mount()
    page = 0

    try:
        while True:
            items = sorted(
                sd.list(),
                key=lambda name: name.lower()
            )

            count = len(items)
            pages = max(
                1,
                (count + PAGE_SIZE - 1) // PAGE_SIZE
            )

            page = min(page, pages - 1)

            show_listing(items, page)

            print()
            print("=== SD FILE MANAGER ===")
            print("Files:", count)
            print("Page:", page + 1, "/", pages)

            start = page * PAGE_SIZE
            end = min(count, start + PAGE_SIZE)

            for idx in range(start, end):
                print("%d. %s" % (idx + 1, items[idx]))

            print()
            print("N = next page")
            print("P = previous page")
            print("Number = open file")
            print("L = list all files")
            print("C = create file")
            print("D = delete file")
            print("B = back")

            cmd = input("SD> ").strip()
            option = cmd.lower()

            if option in ("b", "back", "0"):
                break

            elif option == "n":
                page = (page + 1) % pages

            elif option == "p":
                page = (page - 1) % pages

            elif option == "l":
                for idx, name in enumerate(items):
                    print("%d. %s" % (idx + 1, name))

            elif option == "c":
                name = input(
                    "New relative filename: "
                ).strip()

                if not name:
                    continue

                content = input("Text to save: ")

                sd.write(
                    name,
                    content,
                    overwrite=False
                )

                print("Created:", name)
                message(
                    "CREATED",
                    [short_name(name, 28)]
                )

            elif option == "d":
                if not count:
                    print("No files to delete")
                    continue

                idx = ask_file_number(
                    "File number to DELETE: ",
                    count
                )

                if idx is None:
                    print("Invalid file number")
                    continue

                name = items[idx]

                print("Selected:", name)

                message(
                    "CONFIRM DELETE",
                    [
                        short_name(name, 28),
                        "Type DELETE in REPL"
                    ]
                )

                confirmation = input(
                    "Type DELETE to confirm: "
                ).strip()

                if confirmation == "DELETE":
                    sd.delete(name)
                    print("Deleted:", name)

                    message(
                        "DELETED",
                        [short_name(name, 28)]
                    )
                else:
                    print("Cancelled")

            elif cmd.isdigit() and 1 <= int(cmd) <= count:
                idx = int(cmd) - 1
                name = items[idx]

                # Destacar el archivo seleccionado.
                show_listing(items, idx // PAGE_SIZE, idx)

                # Mostrar el contenido.
                show_file(sd, name)

                input(
                    "Press ENTER for file list..."
                )

                page = idx // PAGE_SIZE

            else:
                print("Unknown option or invalid number")

    finally:
        sd.unmount()


def scan_wifi():
    import network

    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    networks = [
        (result[0], result[3])
        for result in sta.scan()
    ]

    print("Nearby APs:", networks)

    lines = []

    for ssid, rssi in networks[:8]:
        try:
            name = ssid.decode("utf-8")
        except Exception:
            name = repr(ssid)

        lines.append(
            "%s %d dBm" %
            (short_name(name or "(hidden)", 18), rssi)
        )

    message(
        "WIFI SCAN",
        lines or ["No networks found"]
    )


def connect_wifi():
    from connectivity import WiFiManager

    try:
        import secrets
        ssid = secrets.WIFI_SSID
        password = secrets.WIFI_PASSWORD
    except (ImportError, AttributeError):
        print("Create secrets.py with credentials")
        message("WIFI", ["Missing secrets.py"])
        return

    mgr = WiFiManager()
    mgr.connect(ssid, password, 15)

    ip = mgr.wlan.ifconfig()[0]

    print("IP:", ip)
    message("WIFI CONNECTED", [ip])


def radio_status():
    import bluetooth
    import espnow
    import network

    ble = bluetooth.BLE()
    ble.active(True)

    print("BLE stack active:", ble.active())
    ble.active(False)

    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    en = espnow.ESPNow()
    en.active(True)

    print("ESP-NOW initialized (no peer test)")

    en.active(False)

    message(
        "RADIO STATUS",
        [
            "BLE initialized",
            "ESP-NOW initialized",
            "No peer transfer tested"
        ]
    )


def graphics():
    screen("GRAPHICS TEST")

    draw.rectangle(
        2, 34,
        display.WIDTH - 3,
        display.HEIGHT - 3,
        GREEN
    )

    draw.line(
        8, 37,
        display.WIDTH - 9,
        display.HEIGHT - 10,
        CYAN
    )

    draw.circle(
        display.WIDTH // 2,
        78,
        22,
        RED,
        True
    )

    print("Visual drawing done")


def main():
    display.init_display(1)

    message(
        "GEEK CONTROL",
        [
            "1 SD manager",
            "2 WiFi scan",
            "3 Connect WiFi",
            "4 BLE / ESP-NOW",
            "5 Graphics",
            "6 Diagnostic"
        ]
    )

    while True:
        print()
        print("=== GEEK CONTROL ===")
        print("1 SD files")
        print("2 WiFi scan")
        print("3 Connect WiFi")
        print("4 BLE / ESP-NOW")
        print("5 Graphics")
        print("6 Diagnostic")
        print("0 Quit")

        action = input("Select> ").strip()

        if action == "0":
            return

        try:
            if action == "1":
                sd_menu()

            elif action == "2":
                scan_wifi()

            elif action == "3":
                connect_wifi()

            elif action == "4":
                radio_status()

            elif action == "5":
                graphics()

            elif action == "6":
                import geek_diagnostic
                geek_diagnostic.main()
                display.init_display(1)

            else:
                print("Unknown command")

        except Exception as exc:
            print(
                "ERROR:",
                type(exc).__name__,
                str(exc)
            )

            message(
                "ERROR SEE REPL",
                [
                    type(exc).__name__,
                    str(exc)[:29]
                ]
            )

        gc.collect()


if __name__ == "__main__":
    main()

