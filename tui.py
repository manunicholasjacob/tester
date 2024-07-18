import curses
import sbr
import device_control
from datetime import datetime
import gpu_burn_script
import time

def main(stdscr):
    curses.echo()

    # Colors and border setup
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    stdscr.bkgd(curses.color_pair(1))

    # Function to display a box with a title
    def display_box(window, y, x, height, width, title=""):
        window.attron(curses.color_pair(2))
        window.border(0)
        window.addstr(0, 2, f' {title} ')
        window.attroff(curses.color_pair(2))
        window.refresh()

    # Function for Scrollability on the pad
    def scroll_output(window, window_offset_y, window_offset_x, window_height, window_width, pad_pos):
        scroll_pad = pad_pos
        cmd = ''
        while True:
            cmd = window.getch()
            if cmd == ord('q'): break
            if cmd == curses.KEY_DOWN:
                if scroll_pad < pad_pos: scroll_pad += 1
                window.refresh(scroll_pad, 0, window_offset_y, window_offset_x, min(curses.LINES-1, window_offset_y + window_height - 3), min(curses.COLS-1, window_offset_x + window_width - 5))
            elif cmd == curses.KEY_UP:
                if scroll_pad > 0: scroll_pad -= 1
                window.refresh(scroll_pad, 0, window_offset_y, window_offset_x, min(curses.LINES-1, window_offset_y + window_height - 3), min(curses.COLS-1, window_offset_x + window_width - 5))

    # Display available slot numbers
    slot_numbers = sbr.get_slot_numbers()
    gpu_info_list = gpu_burn_script.gpu_traverse_up()

    height = max(len(slot_numbers) + 4, len(gpu_info_list) + 4, 10)

    slot_window_width = 30
    slot_window = curses.newwin(height, slot_window_width, 1, 1)
    display_box(slot_window, 1, 1, height, slot_window_width, "Available Slot Numbers")
    for i, slot in enumerate(slot_numbers):
        slot_window.addstr(i + 2, 2, slot)
    slot_window.refresh()

    gpu_window_height = height  
    gpu_window_width = 70
    gpu_window = curses.newwin(gpu_window_height, gpu_window_width, 1, slot_window_width+3)
    display_box(gpu_window, 1, 41, gpu_window_height, gpu_window_width, "GPU Info")
    for i, gpu_info in enumerate(gpu_info_list):
        gpu_print = f"GPU {i}\t|\tBDF: {gpu_info[0]}\t|\tSlot: {gpu_info[1]}\t|\tRoot Port: {gpu_info[2]}"
        gpu_window.addstr(i+2, 2, gpu_print.expandtabs(3))
    gpu_window.refresh()

    output_window_height = 15
    output_window_width = 50
    output_window = curses.newpad(10000, 50)
    output_window_border = curses.newwin(output_window_height, output_window_width, height + 2, 50+3)
    display_box(output_window_border, 10, 41, height, slot_window_width+3, "Output")
    pad_pos = 0

    # Collect user inputs
    input_window_height = 15
    input_window_width = 50
    input_window = curses.newwin(input_window_height-4, input_window_width-4, height + 4, 3)
    input_window_border = curses.newwin(input_window_height, input_window_width, height + 2, 1)
    display_box(input_window_border, height + 2, 1, input_window_height, input_window_width, "User Inputs")

    input_window.addstr(2-2, 0, "Enter your password (sudo access): ")
    user_password = input_window.getstr().decode()

    input_window.addstr(4-2, 0, "Number of Loops: ")
    inputnum_loops = int(input_window.getstr().decode())

    input_window.addstr(6-2, 0, "Do you want to kill on error? (y/n): ")
    kill = input_window.getstr().decode()

    input_window.addstr(8-2, 0, "Choose slot numbers to test (comma separated): ")
    slot_input = input_window.getstr().decode()
    slotlist = list(map(int, slot_input.split(',')))

    input_window.addstr(10-2, 0, "Choose operation (s: SBR, g: GPU Burn, b: Both): ")
    operation = input_window.getstr().decode().lower()

    input_window.clear()
    input_window.addstr(2-2, 0, f"Password: {'*' * len(user_password)}")
    input_window.addstr(4-2, 0, f"Number of Loops: {inputnum_loops}")
    input_window.addstr(6-2, 0, f"Kill on error: {kill}")
    input_window.addstr(8-2, 0, f"Slot numbers to test: {slotlist}")
    input_window.addstr(10-2, 0, f"Operation: {operation}")
    input_window.addstr(12-2, 0, "Press any key to start the test...")
    input_window.refresh()
    input_window.getch()

    # Set error reporting to 0
    device_window_height = 15
    device_window = curses.newwin(device_window_height, 100, height + 17, 1)
    display_box(device_window, height + 17, 1, device_window_height, 60, "Device Control Status")
    device_window.addstr(2, 2, "Setting error reporting to 0...")
    device_window.refresh()

    bdfs = device_control.get_all_bdfs()
    device_control.store_original_values(bdfs)
    device_control.process_bdfs(bdfs)

    device_window.addstr(4, 2, "Error reporting set to 0.")
    device_window.refresh()

    if operation in ['s', 'b']:
        # Run the sbr functionality
        device_window.addstr(5, 2, "Running SBR tests...")
        device_window.refresh()

        sbr.run_test(device_window, user_password, inputnum_loops, kill, slotlist)

        device_window.addstr(7, 2, "SBR tests completed.")
        device_window.refresh()

    if operation in ['g', 'b']:
        # Run the GPU burn functionality
        for i in range(20):  # Example loop, replace with actual GPU burn logic
            pad_pos = gpu_burn_script.output_print(output_window, height + 3, 55, output_window_height, output_window_width, pad_pos, f"Output line {i}")
            time.sleep(0.2)

        pad_pos = gpu_burn_script.check_replay(95, 10, 4, [], 10, output_window, height + 3, 55, output_window_height, output_window_width, pad_pos)

        scroll_output(output_window, height + 3, 55, output_window_height, output_window_width, pad_pos)

    # Reset device control registers to original values
    device_window.addstr(8, 2, "Resetting device control registers...")
    device_window.refresh()

    device_control.reset_to_original_values()

    device_window.addstr(10, 2, "Device control registers reset to original values.")
    device_window.refresh()

    # Display summary screen
    stdscr.clear()
    display_box(stdscr, 1, 1, 20, 60, "Test Summary")

    try:
        with open("output.txt", "r") as file:
            lines = file.readlines()

        start_time = next(line for line in lines if line.startswith("Start Time:")).split(": ", 1)[1].strip()
        end_time = next(line for line in lines if line.startswith("End Time:")).split(": ", 1)[1].strip()
        tested_bdfs = next(line for line in lines if line.startswith("Tested BDFs:")).split(": ", 1)[1].strip()
        downstream_bdfs = next(line for line in lines if line.startswith("Downstream BDFs:")).split(": ", 1)[1].strip()
        slot_numbers = next(line for line in lines if line.startswith("Slot Numbers:")).split(": ", 1)[1].strip()
        slot_test_counts = next(line for line in lines if line.startswith("Slot Test Counts:")).split(": ", 1)[1].strip()
        errors = [line for line in lines if "Error" in line]

        total_time = (datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds()

        stdscr.addstr(2, 2, f"Start Time: {start_time}")
        stdscr.addstr(3, 2, f"End Time: {end_time}")
        stdscr.addstr(4, 2, f"Total Time Taken: {total_time:.2f} seconds")
        stdscr.addstr(5, 2, f"Tested BDFs: {tested_bdfs}")
        stdscr.addstr(6, 2, f"Downstream BDFs: {downstream_bdfs}")
        stdscr.addstr(7, 2, f"Slot Numbers: {slot_numbers}")
        stdscr.addstr(8, 2, f"Slot Test Counts: {slot_test_counts}")
        if errors:
            stdscr.addstr(9, 2, f"Errors: {len(errors)}")
            for i, error in enumerate(errors[:5], start=10):  # Display up to 5 errors
                stdscr.addstr(i, 2, error.strip())
        else:
            stdscr.addstr(9, 2, "No errors detected.")
    except Exception as e:
        stdscr.addstr(2, 2, f"Error reading summary: {str(e)}")

    stdscr.refresh()
    stdscr.getch()  # Wait for a key press to keep the interface open

curses.wrapper(main)
