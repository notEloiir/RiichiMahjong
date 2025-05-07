from ml.src.data_structures.dataset import DataSet


# Functionality should mirror refine_data.ipynb
def refine_data(raw_data_filename, refined_data_filename):
    dataset_raw = DataSet.from_file(raw_data_filename)

    print("refine_data not implemented, for now just copies from raw_data_filename to refined_data_filename")
    dataset_raw.save(refined_data_filename)
