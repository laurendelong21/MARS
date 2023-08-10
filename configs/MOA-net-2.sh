input_dir="datasets/MOA-net/"
base_output_dir="output/MOA-net/"
update_confs=2
alpha="0.01 0.05 0.1 0.5 0.75"
path_length=3
total_iterations=1000
eval_every=10
patience=2
rule_base_reward=3
only_body=0
embedding_size=32
hidden_size=32
LSTM_layers=2
beta=0.05
Lambda=0.02
learning_rate=0.0006
max_num_actions=400
train_entity_embeddings=1
use_entity_embeddings=1
num_rollouts=30
load_model=0
model_load_path="./models/MOA-net/model.ckpt"
