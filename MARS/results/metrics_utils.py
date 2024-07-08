import os.path as osp
import statistics
import os
import pandas as pd


def get_metrics_dict(experiment_dir):
    """Pass the path of a directory for a single experiment (which might contain multiple runs/replicates)

    :param experiment_dir: directory for a single experiment (which might contain multiple runs/replicates)
    :returns: a dictionary of the metric names to their average and standard deviation
    """
    exp_name = osp.basename(experiment_dir)

    # all experimental runs
    runs = os.listdir(experiment_dir)

    hits_values = {"Hits@1": [], "Hits@3": [], "Hits@10": [], "MRR": []}
    pruned_values = {
        "Hits@1_rule": [],
        "Hits@3_rule": [],
        "Hits@10_rule": [],
        "MRR_rule": [],
    }

    for run in runs:
        if not osp.isdir(osp.join(experiment_dir, run)):
            continue
        # for each run in an experiment dir, get the paths dir
        fpath = osp.join(experiment_dir, f"{run}/scores.txt")

        # Open the file for reading
        with open(fpath, "r") as file:
            # Read the file line by line
            for line in file:
                split_line = line.split(":")
                # Find each metric
                if split_line[0] in set(hits_values.keys()):
                    hits_values[split_line[0]].append(float(split_line[1].strip()))
                elif split_line[0] in set(pruned_values.keys()):
                    pruned_values[split_line[0]].append(float(split_line[1].strip()))

    hits_values = {
        key: (round(sum(val) / len(val), 3), round(statistics.stdev(val), 3))
        for key, val in hits_values.items()
    }
    pruned_values = {
        key.split("_rule")[0]: (
            round(sum(val) / len(val), 3),
            round(statistics.stdev(val), 3),
        )
        for key, val in pruned_values.items()
    }

    scores = {f"{exp_name}": hits_values, f"{exp_name} (pruned)": pruned_values}

    return scores


def process_polo_metrics(results_dir):
    """Gets and formats the metrics from MARS into a table. Simply pass a directory with multiple experiments in it,
    and this will compute the average and stdev
    """
    final_metrics = dict()

    # all experimental runs
    experiments = os.listdir(results_dir)

    for exp in experiments:
        exp_path = osp.join(results_dir, exp)
        if not osp.isdir(exp_path):
            continue
        # for each experiment dir, get the metrics dict
        metrics_dict = get_metrics_dict(exp_path)
        for key, val in metrics_dict.items():
            final_metrics[key] = val

    metrics_df = pd.DataFrame(final_metrics).transpose().sort_index()

    # Write the rounded DataFrame to a TSV file
    output_file = osp.join(results_dir, "metrics.tsv")
    metrics_df.to_csv(output_file, sep="\t", index=True)