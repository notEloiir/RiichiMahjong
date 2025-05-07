import os

from ml.src.data_structures import DataPoint, MatchData
from ml.src.data_structures.dataset import DataSet
from ml.src.data_processing.db_connect import get_match_log_data
from ml.src.data_processing.parse_logs import parse_match_log
from game.src.core.match import run_match


def extract_datapoints(db_filename, raw_data_filename, how_many=500):
    db_path = os.path.join(os.getcwd(), "phoenix-logs", "db")
    cursor, match_no = get_match_log_data(db_path, db_filename)
    print(f"Available {match_no} matches")

    datapoints: list[DataPoint] = []
    match_replays: list[MatchData] = []
    if how_many <= 0 or how_many >= match_no:
        how_many = match_no
    for match_log in cursor.fetchmany(how_many):
        match_replay = parse_match_log(match_log[0], min_dan=16)
        if match_replay is not None:
            match_replays.append(match_replay)
    print("Parsed logs")

    for i, match_replay in enumerate(match_replays):
        data = None
        try:
            _, data = run_match(None, match_replay=match_replay, collect_data=True)
        except Exception as e:
            # Due to the bugs' obscurity, rarity and limited time this is good enough
            # From what I gather mostly due to differences in how a winning hand is counted
            pass

        if data is not None:
            datapoints.extend(data)
            
        if (i + 1) % 100 == 0:
            print(f"{i + 1}/{how_many}")
    print(f"Extracted {len(datapoints)} datapoints")

    dataset = DataSet.from_datapoints(datapoints)
    dataset.save(raw_data_filename)
    print("Saved dataset")
