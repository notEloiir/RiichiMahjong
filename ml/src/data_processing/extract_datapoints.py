import os
import math

from ml.src.data_structures import DataPoint, MatchData
from ml.src.data_structures.dataset import DataSet
from ml.src.data_processing.db_connect import get_match_log_data
from ml.src.data_processing.parse_logs import parse_match_log
from game.src.core.match import run_match


def extract_datapoints(db_filename, raw_data_filename, how_many=1000, chunk_size=6000):
    db_path = os.path.join(os.getcwd(), "phoenix-logs", "db")
    cursor, match_no = get_match_log_data(db_path, db_filename)
    print(f"Available {match_no} matches")
    if how_many <= 0 or how_many >= match_no:
        how_many = match_no
    n_chunks = math.ceil(how_many / chunk_size)
    print(f"Using {how_many} matches in {n_chunks} chunks")

    for chunk_i in range(n_chunks):
        fetch_how_many = chunk_size
        if chunk_i + 1 == n_chunks and how_many // chunk_size < n_chunks:
            fetch_how_many = how_many % chunk_size
        datapoints: list[DataPoint] = []
        match_replays: list[MatchData] = []
        for match_log in cursor.fetchmany(fetch_how_many):
            match_replay = parse_match_log(match_log[0], min_dan=16)
            if match_replay is not None:
                match_replays.append(match_replay)
        print(f"Chunk {chunk_i+1}/{n_chunks}: parsed logs")

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

        print(f"Chunk {chunk_i+1}/{n_chunks}: {len(datapoints)} datapoints extracted")
        # save every 6000 matches results in parquet files ~100MiB
        DataSet.save_batch(datapoints, raw_data_filename)
        datapoints.clear()
        print(f"Chunk {chunk_i+1}/{n_chunks}: saved")
