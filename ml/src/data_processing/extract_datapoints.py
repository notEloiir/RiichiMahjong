import os
import math

from ml.src.data_structures import DataPoint, MatchData
from ml.src.data_structures.dataset import DataSet
from ml.src.data_processing.db_connect import get_match_log_data
from ml.src.data_processing.parse_logs import parse_match_log
from game.src.core.match import run_match


def extract_datapoints(db_filename, raw_data_filename, ds_part_size=1e4):
    db_path = os.path.join(os.getcwd(), "phoenix-logs", "db")
    cursor, match_no = get_match_log_data(db_path, db_filename)
    dataset = DataSet(raw_data_filename)
    ds_part_size = int(ds_part_size)
    print(f"Available {match_no} matches, {math.ceil(match_no / ds_part_size)} batches")

    for batch in range(math.ceil(match_no / ds_part_size)):
        how_many = ds_part_size if batch == match_no // ds_part_size else match_no % ds_part_size
        match_replays: list[MatchData] = []
        for match_log in cursor.fetchmany(how_many):
            match_replay = parse_match_log(match_log[0], min_dan=16)
            if match_replay is not None:
                match_replays.append(match_replay)

        datapoints: list[DataPoint] = []
        for match_replay in match_replays:
            data = None
            try:
                _, data = run_match(None, match_replay=match_replay, collect_data=True)
            except Exception as e:
                # Due to the bugs' obscurity, rarity and limited time this is good enough
                # From what I gather mostly due to differences in how a winning hand is counted
                pass

            if data is not None:
                datapoints.extend(data)
        print(f"Batch {batch + 1}/{math.ceil(match_no / ds_part_size)}: {len(datapoints)}")

        if datapoints:
            dataset.save_batch(datapoints)
