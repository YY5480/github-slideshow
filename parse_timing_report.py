import re

def analyze_timing_report(file_path):
    '''
    Parses a timing report file to extract key metrics.

    Args:
        file_path (str): The path to the timing report file.

    Returns:
        dict: A dictionary containing the extracted information,
              or None if parsing fails.
    '''
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None

    # --- Extraction using regular expressions ---
    startpoint_match = re.search(r"Startpoint:\s*(\w+)", content)
    endpoint_match = re.search(r"Endpoint:\s*(\w+)", content)
    slack_match = re.search(r"slack\s*\(.*\)\s*(-?\d+\.\d+)", content)
    if not slack_match: # Handle cases where there's no status like (VIOLATED)
        slack_match = re.search(r"slack\s+(-?\d+\.\d+)", content)


    startpoint = startpoint_match.group(1) if startpoint_match else "Not Found"
    endpoint = endpoint_match.group(1) if endpoint_match else "Not Found"

    if slack_match:
        # The slack value is the last captured group
        slack = float(slack_match.groups()[-1])
    else:
        slack = "Not Found"


    # --- Path and Cell Count Extraction ---
    path = []
    cell_count = 0
    # The data path is in the section starting after the 'Point' header
    # and ending before 'data arrival time'
    path_section_match = re.search(
        r"Point\s+Cap[\s\S]*?-{10,}\n([\s\S]*?)^data arrival time",
        content,
        re.MULTILINE
    )

    if path_section_match and startpoint != "Not Found" and endpoint != "Not Found":
        path_block = path_section_match.group(1)
        lines = path_block.strip().split('\n')

        in_data_path = False
        for line in lines:
            line = line.strip()
            if not line or len(line.split()) < 1:
                continue

            point = line.split()[0]

            # Data path starts at the output pin of the start flop (e.g., /Q)
            if startpoint in point and "/Q" in point:
                in_data_path = True

            if in_data_path:
                path.append(point)
                # Data path ends at the input pin of the end flop (e.g., /D)
                if endpoint in point and "/D" in point:
                    break

    # The cell count will now only include intermediate cells.
    cell_count = 0
    if len(path) > 2:
        cell_count = len(path) - 2

    return {
        "startpoint": startpoint,
        "endpoint": endpoint,
        "path": path,
        "cell_count": cell_count,
        "slack": slack
    }

if __name__ == "__main__":
    report_data = analyze_timing_report('timing_report.txt')

    if report_data:
        print("--- Timing Analysis Report ---")
        print(f"Startpoint: {report_data['startpoint']}")
        print(f"Endpoint: {report_data['endpoint']}")

        if report_data['path']:
            print(f"Path: {' -> '.join(report_data['path'])}")
            print(f"Intermediate Cell Count: {report_data['cell_count']}")
        else:
            print("Path: Could not be determined.")

        print(f"Slack: {report_data['slack']}")
        print("------------------------------")
