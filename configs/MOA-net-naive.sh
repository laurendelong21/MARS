input_dir="datasets/MOA-net/"
base_output_dir="output/MOA-net-naive/"
update_confs=1
alpha=0.001
path_length=3
total_iterations=1000
eval_every=10
patience=2
rule_base_reward=1
only_body=0
embedding_size=256
hidden_size=64
LSTM_layers=2
beta=0.05
Lambda=0.5
learning_rate=0.0001
max_num_actions=150
train_entity_embeddings=1
use_entity_embeddings=1
batch_size=256
num_rollouts=100
test_rollouts=100
load_model=0
model_load_path="./models/MOA-net-naive/model.ckpt"
