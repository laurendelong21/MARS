

<h1 align="center">
Mechanism-of-Action Retrieval System (MARS)
<br>
</h1>

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)]()
![Maturity level-1](https://img.shields.io/badge/Maturity%20Level-ML--1-yellow)
[![PyPI pyversions](https://img.shields.io/badge/python-%3E%3D3.8-brightgreen)](https://img.shields.io/badge/python-%3E%3D3.8-brightgreen)

This is the code corresponding to MARS, the mechanism-of-action retrieval system for drug discovery.

Ready to run? :arrow_right: Jump directly to [**running MARS**](#run).

<h2> Installation and Setup </h2>

<h3>  Installation: </h3>

Clone or move the MARS repository to the desired location. Then, create a virtual environment via the next steps.

<h3>  Dependencies and Virtual Environment: </h3>

The dependencies are specified in [ENV.yml](ENV.yml) as well as [requirements.txt](requirements.txt) The user can use either of the following to create
a virtual environment:

```
conda env create -n ENV_NAME --file ENV.yml
```

```
python3 -m venv env

source env/bin/activate

pip install -r requirements.txt
```

<h2> Data Format </h2>

<h3> MoA-Net </h3>

The creation of MoA-Net is within the `MoA-Net` repository. This is the other repository included within this zip file. Links are hidden for anonymity.

:100: MoA-Net data files are *ready to run*. To skip data formatting instructions, jump directly to [**running MARS**](#run).

<h3> Triple format </h3>

- KG triples need to be written in the format ```subject predicate object```, with tabs as separators.
- Furthermore, MARS uses inverse relations, so it is important to add the inverse triple for each fact in the KG. 
    - The prefix  ```_``` is used before a predicate to signal the inverse relation
    - e.g., the inverse triple for ```Drug induces Biological Process``` is ```Drug _induces Biological Process```.

<h3> File format </h3>

Each dataset directory should have the following structure:
```
dataset_name
    ├── train.txt
    ├── dev.txt
    ├── test.txt
    ├── graph.txt
    └── rules.txt
    └── vocab
        └── entity_vocab.json
        └── relation_vocab.json
        └── meta_mapping.json
    └── validation_paths.json
```

Where:

- ```train.txt``` contains all positive triples to predict in the training set.

- ```dev.txt``` contains all positive triples to predict in the validation set.

- ```test.txt``` contains all positive triples to predict in the test set.

- ```graph.txt``` contains all triples of the KG except for ```dev.txt```, ```test.txt```, the inverses of ```dev.txt```, and the inverses of ```test.txt```.

    **NOTE** for the generation of ```graph.txt```:

    For *MoA-Net*, the complete graph is split into ```graph_triples.txt``` (forward triples) and ```graph_inverses.txt``` (inverse triples) because of the file size constraints on GitHub.

    These two files **need to be combined into one file** (with the name ```graph.txt```) before running the code.

    To do this, you have to create a file called ```graph.txt```, as explained above:

    ```
    cat datasets/MOA-net/graph_triples.txt datasets/MOA-net/graph_inverses.txt > datasets/MOA-net/graph.txt
    ```

- ```rules.txt``` contains the rules as a dictionary, where the keys are the head relations. The rules for a specific relation are stored as a list of lists (sorted by decreasing confidence), where a rule is denoted as ```[confidence, head relation, body relation, ..., body relation]```.

- the ```vocab/``` directory contains two mandatory files, and, if the user wishes, one additional files:

    - ```entity_vocab.json``` is a dictionary mapping each node / entity to a unique integer ID

    - ```relation_vocab.json``` is a dictionary mapping each relation / edge type to a unique integer ID

    - (optional) ```meta_mapping.json``` is only used in the results processing step. It is a dictionary mapping each node and edge type to a longer word, in case it is abbreviated in the dataset (e.g., ```"C": "Compound"```).

- (optional) ```validation_paths.json``` is also exclusively for the results processing steps. It can be included if there are certain paths, such as drug mechanisms-of-action, which should also be checked amonst the test-set paths. In other words, "did the agent traverse these specific paths between these pairs of nodes?"

<h3>  Hyperparameter Configurations: </h3>

To run MARS, use one of the config files or create your own. For an explanation of each hyperparameter, refer to the [README file in the configs folder](configs/README.md).


<h2> Run MARS: </h2>
<a name="run"></a>

Once you're ready to run MARS, use the `run.sh` bash script, followed by the proper configuration file:

```
cd PoLo

./run.sh configs/${config_file}.sh
```

The permissions for the ```run.sh``` file are typically editable for all, but in case they aren't, run:
```
chmod a+x ./run.sh
```

If you want to run replicates of the same configuration, you can use the replicates bash script, with the first argument being the configuration file, and the second being the number of replicates:

```
cd PoLo

./replicates.sh configs/${config_file}.sh {n_replicates}
```

<h2> MARS in Replicates: </h2>

MARS also includes a results analysis module, which can be run if 2+ iterations have been run within a folder.

For instance, if the user ran 5 iterations of a certain configuration:

```
./replicates.sh configs/${config_file}.sh 5
```

<h3> Analyze Results: </h3>

If replicates are conducted, the user could then analyze the results within the corresponding directory, simply by running the following for the same configuration file:

```
./process_results.sh configs/${config_file}.sh
```

**Note** that this analysis only works with > 1 replicate.


<h2> Implementation:</h2>

This implementation is based on code from: 
- [PoLo (Neural Multi-Hop Reasoning With Logical Rules on Biomedical Knowledge Graphs)](https://arxiv.org/abs/2103.10367), which is also based upon 
- [MINERVA](https://github.com/shehzaadzd/MINERVA) from the paper [Go for a Walk and Arrive at the Answer - Reasoning over Paths in Knowledge Bases using Reinforcement Learning](https://arxiv.org/abs/1711.05851).
