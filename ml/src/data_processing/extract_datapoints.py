import os

from ml.src.data_structures import DataPoint, MatchData
from ml.src.data_structures.dataset import DataSet
from ml.src.data_processing.db_connect import get_match_log_data
from ml.src.data_processing.parse_logs import parse_match_log
from game.src.core.match import run_match


def extract_datapoints(db_filename, raw_data_filename, batch_size=500):
    db_path = os.path.join(os.getcwd(), "phoenix-logs", "db")
    cursor, match_no = get_match_log_data(db_path, db_filename)
    dataset = DataSet(raw_data_filename)
    print(f"Available {match_no} matches, {((match_no - 1) // batch_size) + 1} batches")

    for batch in range(((match_no - 1) // batch_size) + 1):
        how_many = batch_size if batch == match_no // batch_size else match_no % batch_size
        match_replays: list[MatchData] = []
        for match_log in cursor.fetchmany(how_many):
            match_replay = parse_match_log(match_log[0])
            if match_replay is not None:
                match_replays.append(match_replay)

        datapoints: list[DataPoint] = []
        for match_replay in match_replays:
            _, data = run_match(None, match_replay=match_replay, collect_data=True)
            datapoints.extend(data)

        if datapoints:
            dataset.save_batch(datapoints)
