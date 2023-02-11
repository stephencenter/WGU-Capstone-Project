import os
import pandas
import tensorflow
import streamlit
import sklearn.model_selection
from tensorflow import keras

model_path = "tensorflow_model"

def load_data():
    training_dataframe = pandas.read_csv('training_data.csv')
    training_dataframe = training_dataframe.set_index('player_id')

    training_x = training_dataframe.drop('in_hall_of_fame', axis=1)
    training_y = training_dataframe['in_hall_of_fame']

    player_dataframe = pandas.read_csv('player_data.csv')
    player_dataframe = player_dataframe.set_index('player_id')

    return training_x, training_y, player_dataframe

def prepare_data(training_x, training_y):
    train_data, test_data, train_labels, test_labels = sklearn.model_selection.train_test_split(training_x, training_y, test_size=0.25, random_state=256)

    data_scaler = sklearn.preprocessing.StandardScaler()
    train_data_scaled = data_scaler.fit_transform(train_data)
    test_data_scaled = data_scaler.transform(test_data)

    return train_data_scaled, train_labels, test_data_scaled, test_labels, data_scaler

def create_model():
    new_model = keras.Sequential([
        keras.layers.Dense(256, activation='relu'),
        keras.layers.Dense(256, activation='relu'),
        keras.layers.Dense(1, activation='sigmoid')
    ])

    new_model.compile(
        loss=keras.losses.binary_crossentropy,
        optimizer=keras.optimizers.RMSprop(),
        metrics=[
            keras.metrics.BinaryAccuracy(name='accuracy'),
            keras.metrics.Precision(name='precision'),
            keras.metrics.Recall(name='recall')
        ]
    )

    return new_model

def train_model(model, train_data_scaled, train_labels, test_data_scaled, test_labels):
    model.fit(
        train_data_scaled,
        train_labels,
        epochs=20,
        validation_data=(test_data_scaled, test_labels)
    )

def evaluate_model(model, test_data, test_labels):
    t_pos = 0
    t_neg = 0
    f_neg = 0
    f_pos = 0

    predictions = model.predict(test_data)
    for index, pair in enumerate(zip(test_labels, predictions)):
        if pair[1] > 0.5:
            if pair[0] == 0:
                f_pos += 1
            else:
                t_pos += 1

        else:
            if pair[0] == 0:
                t_neg += 1
            else:
                f_neg += 1

    accuracy = (t_pos + t_neg)/(t_pos + t_neg + f_pos + f_neg)
    precision = t_pos/(t_pos + f_pos)
    recall = t_pos/(t_pos + f_neg)
    return accuracy, precision, recall

def get_user_input():
    column_1, column_2, column_3 = streamlit.columns(3)
    with column_1:
        war = streamlit.number_input("Wins Above Replacement (WAR)", value=0.0, min_value=-10.0, step=0.1, format="%.1f")
        batter_average = streamlit.number_input("Batting Average (BA)", min_value=0.0, max_value=1.0, step=0.001, format="%.3f")
        batter_obp = streamlit.number_input("On-base Percentage (OBP)", min_value=0.0, max_value=1.0, step=0.001, format="%.3f")
        pitcher_losses = streamlit.number_input("Losses as pitcher (L)", min_value=0, step=1)
        pitcher_innings = streamlit.number_input("Innings pitched (IP)", min_value=0.0, step=0.1, format="%.1f")

    with column_2:
        batter_atbats = streamlit.number_input("At bats (AB)", min_value=0, step=1)
        batter_runs = streamlit.number_input("Runs (R)", min_value=0, step=1)
        batter_slugging = streamlit.number_input("Slugging Average (SLG)", min_value=0.0, max_value=4.0, step=0.001, format="%.3f")
        pitcher_era = streamlit.number_input("Earned Run Average (ERA)", min_value=0.0, step=0.01, format="%.2f")
        pitcher_whip = streamlit.number_input("Walks + Hits per Inning Pitched (WHIP)", min_value=0.0, step=0.001, format="%.3f")

    with column_3:
        batter_homeruns = streamlit.number_input("Home runs (HR)", min_value=0, step=1)
        batter_rbi = streamlit.number_input("Runs Batted In (RBI)", min_value=0, step=1)
        pitcher_wins = streamlit.number_input("Wins as pitcher (W)", min_value=0, step=1)
        pitcher_saves = streamlit.number_input("Saves (SV)", min_value=0, step=1)
        allstar_apps = streamlit.number_input("All-Star Game Appearances", min_value=0, step=1)


    return {
        "batter_atbats": batter_atbats,
        "batter_homeruns": batter_homeruns,
        "batter_obp": batter_obp,
        "batter_slugging": batter_slugging,
        "batter_runs": batter_runs,
        "batter_rbi": batter_rbi,
        "batter_average": batter_average,
        "pitcher_innings": pitcher_innings,
        "pitcher_wins": pitcher_wins,
        "pitcher_losses": pitcher_losses,
        "pitcher_era": pitcher_era,
        "pitcher_whip": pitcher_whip,
        "pitcher_saves": pitcher_saves,
        "war": war,
        "allstar_apps": allstar_apps
    }

def main():
    tensorflow.random.set_seed(128)
    percentage = lambda x: round(float(x)*100, 2)

    training_x, training_y, player_dataframe = load_data()
    train_data_scaled, train_labels, test_data_scaled, test_labels, data_scaler = prepare_data(training_x, training_y)

    model = create_model()

    if os.path.exists(model_path):
        model = keras.models.load_model(model_path)

    else:
        train_model(model, train_data_scaled, train_labels, test_data_scaled, test_labels)
        model.save(model_path)


    streamlit.title("Hall of Fame Calculator")
    streamlit.write("Input a player's stats and an AI will predict if that player would be elected to the Baseball Hall of Fame")
    user_input = get_user_input()
    user_stats = pandas.DataFrame(user_input, index=["user"])
    user_stats_scaled = data_scaler.transform(user_stats)

    hof_prediction = model.predict(user_stats_scaled)
    streamlit.subheader(f"The chance that a player with the above stats would be elected to the hall of fame is...")
    streamlit.subheader(f"...{percentage(hof_prediction)}%")

    streamlit.subheader("Model Evaluation:")
    accuracy, precision, recall = evaluate_model(model, test_data_scaled, test_labels)
    streamlit.write(f"Accuracy: {percentage(accuracy)}%")
    streamlit.write(f"Precision: {percentage(precision)}%")
    streamlit.write(f"Recall: {percentage(recall)}%")

if __name__ == "__main__":
    main()