# Parameter Configuration

```--input_dir```: str. Directory path where the ```graph.txt```, ```train.txt```, ```dev.txt```, and ```test.txt``` files are
located.

```--base_output_dir```: str. Base directory path where the results of the experiment should be saved to.

```--rule_file```: str. Name of the file containing the rules in the input directory.

```--pretrained_embeddings_dir```: str. Directory path where pretrained embeddings (```.npy``` files) are saved. The corresponding entity-to-id and relation-to-id mappings should also be included in this directory.

```--load_model```: int. Either 0 or 1. Flag to check whether a trained model should be loaded and tested. Setting this value to 1 skips the training and directly tests the model.

```--model_load_path```: str. Directory path where the model is saved. The path should directly point towards the ```.ckpt``` file, and the file should be called ```model.ckpt```.

```--total_iterations```: int. Number of total iterations/episodes during training.

```--eval_every```: int. How often the current model should be tested on the ```dev``` set. The model is only saved after the validation, so ```eval_every``` should be less than ```total_iterations```. Only if the performance on the validation set increases, the model is overwritten.

```--patience```: int. Number of iterations to wait before stopping training (early stopping) if the performance on the validation set does not increase.

```--seed```*: int. Random seed for reproducibility.

```--batch_size```*: int. Size of the sampled batch by the [RelationEntityBatcher](../mycode/data/feed_data.py).

```--num_rollouts```*: int. Number of rollouts for each query during training.

```--test_rollouts```*: Number of rollouts for each query during testing.

```--path_length```*: int. Length of the extracted path.

```--max_num_actions```*: int. Maximum branching factor for the knowledge graph created by the [RelationEntityGrapher](../mycode/data/grapher.py). This limits the maximum number of actions available to the agents at each step.

```--hidden_size```*: int. Influences the size of the hidden layers in the LSTM and MLP.

```--embedding_size```*: int. Size of the relation and entity embeddings.

```--LSTM_layers```*: int. Number of LSTM layers.

```--learning_rate```*: float. Learning rate of the optimizer.

```--beta```*: float. Entropy regularization factor.

```--gamma```*: float. Discount factor for REINFORCE.

```--Lambda```*: float. Discount factor for the baseline. This is lambda in the reward function.

```--grad_clip_norm```*: int. Clipping ratio for the gradient.

```--rule_base_reward```*: int. The base reward that is used to calculate the reward when a rule is applied.

```--positive_reward```*: float. Positive reward if the end entity is correct.

```--negative_reward```*: float. Negative reward if the end entity is incorrect.

```--only_body```*: int. Either 0 or 1. Flag to check whether the extracted paths should only be compared against the body of the rules, or if the correctness of the end entity should also be taken into account. 

This is b in the reward function; 0 means we set it equal to the first term, and 1 means we set it equal to 1.

```--pool```*: str. ```max``` or ```sum```. Pooling operation for evaluation.

```--use_entity_embeddings```: int. Either 0 or 1. Flag to check whether the paths should use the entity embeddings.

```--train_entity_embeddings```*: int. Either 0 or 1. Flag to check whether the entity embeddings should be trained after initialization.

```--train_relation_embeddings```*: int. Either 0 or 1. Flag to check whether the relation embeddings should be trained  after initialization.

```--update_confs```: int. Either 0, 1, or 2. Option to determine whether and how the confidence values should be updated. 0 means no updates, 1 means frequency-based (naive) updates, 2 means 2-hop joint probabilities (P2H), and 3 means a mix between the two confidence update methods.

```--mixing_ratio```*: float. This only does something when update_confs == 3. This is the ratio of the confidence update which is composed of the frequency-based update. IOW, a mixing_ratio > 0.5 means that the frequency-based update will be taken into account more than the P2H update. 0.5 means equal mixing. Default is 0.5.

```--alpha```*: float. Some number between 0-1 indicating how strongly or dramatically the confidence updates should be made. 0 would be the equivalent of choosing update_confs of 0. 


Arguments marked with a ```*``` also take as values a list of the corresponding type written as string,
e.g., ```path_length="1 2 3"```. A grid search across all combinations is then carried out.  
