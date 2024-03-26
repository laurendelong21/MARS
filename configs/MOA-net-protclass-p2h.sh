input_dir="datasets/MOA-net-protclass/"
base_output_dir="output/MOA-net-protclass-p2h/"
update_confs=2
alpha="0.001 0.01"
path_length=3
total_iterations=1000
eval_every=10
patience=2
rule_base_reward=3
only_body=0
embedding_size=256
hidden_size=64
LSTM_layers=2
beta=0.05
Lambda=0.5
learning_rate="0.0001 0.001"
max_num_actions=150
train_entity_embeddings=1
use_entity_embeddings=1
batch_size=256
num_rollouts=50
test_rollouts=100
load_model=0
model_load_path="./models/MOA-net-protclass-p2h/model.ckpt"
