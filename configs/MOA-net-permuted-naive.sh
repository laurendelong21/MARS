input_dir="datasets/MOA-net-permuted/"
base_output_dir="output/MOA-net-permuted-naive/"
update_confs=1
alpha=0.01
path_length=3
total_iterations=1000
eval_every=10
patience=2
Lambda=2
only_body=0
embedding_size=256
hidden_size=64
LSTM_layers=2
beta=0.05
gamma_baseline=0.05
learning_rate=0.0001
max_branching=150
train_entity_embeddings=1
use_entity_embeddings=1
batch_size=128
num_rollouts=100
test_rollouts=100
load_model=0
model_load_path="./models/MOA-net-permuted-naive/model.ckpt"
