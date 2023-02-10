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

def analyze_data(player_dataframe : pandas.DataFrame):
    mean_data = dict()
    for key in player_dataframe.keys():
        nonzeros = [val for val in player_dataframe[key] if not isinstance(val, str) and val != 0]
        try:
            mean_data[key] = sum(nonzeros) / len(nonzeros)
        except ZeroDivisionError:
            pass

    hof_mean_data = {key: [] for key in player_dataframe.keys()}
    for player in player_dataframe.iterrows():
        player_data = player[1]

        if not player_data["in_hall_of_fame"]:
            continue

        for stat in player_data.keys():
            value = player_data[stat]
            if not isinstance(value, str) and value != 0:
                hof_mean_data[stat].append(value)

    for key in list(hof_mean_data):
        try:
            hof_mean_data[key] = sum(hof_mean_data[key]) / len(hof_mean_data[key])
        except ZeroDivisionError:
            del hof_mean_data[key]

    return mean_data, hof_mean_data

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

def test_model(model, test_data, test_labels):
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
    streamlit.write(f"Accuracy: {round(accuracy*100, 2)}%, T-Pos: {t_pos}, T-Neg: {t_neg}, F-Pos: {f_pos}, F-Neg: {f_neg}")

def create_bar_graph(mean_stats, hof_mean_stats, index, value, text):
    with streamlit.expander(f"Compare {text}"):
        streamlit.bar_chart({"You": {"Your Input": value}, "All": mean_stats[index], "HOF": hof_mean_stats[index]})

def get_user_input(mean_stats, hof_mean_stats):
    column_1, column_2, column_3 = streamlit.columns(3)
    with column_1:
        war = streamlit.number_input("Wins Above Replacement (WAR)", value=0.0, min_value=-10.0, step=0.1, format="%.1f")
        create_bar_graph(mean_stats, hof_mean_stats, "war", war, "WAR")

        batter_average = streamlit.number_input("Batting Average (BA)", min_value=0.0, max_value=1.0, step=0.001, format="%.3f")
        create_bar_graph(mean_stats, hof_mean_stats, "batter_average", batter_average, "Batting Average")

        batter_obp = streamlit.number_input("On-base Percentage (OBP)", min_value=0.0, max_value=1.0, step=0.001, format="%.3f")
        create_bar_graph(mean_stats, hof_mean_stats, "batter_obp", batter_obp, "OBP")

        pitcher_losses = streamlit.number_input("Losses as pitcher (L)", min_value=0, step=1)
        create_bar_graph(mean_stats, hof_mean_stats, "pitcher_losses", pitcher_losses, "Losses")

        pitcher_innings = streamlit.number_input("Innings pitched (IP)", min_value=0.0, step=0.1, format="%.1f")
        create_bar_graph(mean_stats, hof_mean_stats, "pitcher_innings", pitcher_innings, "Innings Pitched")

    with column_2:
        batter_atbats = streamlit.number_input("At bats (AB)", min_value=0, step=1)
        create_bar_graph(mean_stats, hof_mean_stats, "batter_atbats", batter_atbats, "At bats")

        batter_runs = streamlit.number_input("Runs (R)", min_value=0, step=1)
        create_bar_graph(mean_stats, hof_mean_stats, "batter_runs", batter_runs, "Runs")

        batter_slugging = streamlit.number_input("Slugging Average (SLG)", min_value=0.0, max_value=4.0, step=0.001, format="%.3f")
        create_bar_graph(mean_stats, hof_mean_stats, "batter_slugging", batter_slugging, "SLG")

        pitcher_era = streamlit.number_input("Earned Run Average (ERA)", min_value=0.0, step=0.01, format="%.2f")
        create_bar_graph(mean_stats, hof_mean_stats, "pitcher_innings", pitcher_innings, "Innings Pitched")

        pitcher_whip = streamlit.number_input("Walks + Hits per Inning Pitched (WHIP)", min_value=0.0, step=0.001, format="%.3f")
        create_bar_graph(mean_stats, hof_mean_stats, "pitcher_whip", pitcher_whip, "WHIP")

    with column_3:
        batter_homeruns = streamlit.number_input("Home runs (HR)", min_value=0, step=1)
        create_bar_graph(mean_stats, hof_mean_stats, "batter_homeruns", batter_homeruns, "Home runs")

        batter_rbi = streamlit.number_input("Runs Batted In (RBI)", min_value=0, step=1)
        create_bar_graph(mean_stats, hof_mean_stats, "batter_rbi", batter_rbi, "RBI")

        pitcher_wins = streamlit.number_input("Wins as pitcher (W)", min_value=0, step=1)
        create_bar_graph(mean_stats, hof_mean_stats, "pitcher_wins", pitcher_wins, "Wins")

        pitcher_saves = streamlit.number_input("Saves (SV)", min_value=0, step=1)
        create_bar_graph(mean_stats, hof_mean_stats, "pitcher_saves", pitcher_saves, "Saves")

        allstar_apps = streamlit.number_input("All-Star Game Appearances", min_value=0, step=1)
        create_bar_graph(mean_stats, hof_mean_stats, "allstar_apps", allstar_apps, "All-Star Games")


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

    training_x, training_y, player_dataframe = load_data()
    train_data_scaled, train_labels, test_data_scaled, test_labels, data_scaler = prepare_data(training_x, training_y)

    model = create_model()

    if os.path.exists(model_path):
        model = keras.models.load_model(model_path)

    else:
        train_model(model, train_data_scaled, train_labels, test_data_scaled, test_labels)
        model.save(model_path)

    test_model(model, test_data_scaled, test_labels)

    mean, hof_mean = analyze_data(player_dataframe)
    mean_stats = pandas.DataFrame(mean, index=["Average (All)"])
    hof_mean_stats = pandas.DataFrame(hof_mean, index=["Average (HOF)"])

    user_stats = pandas.DataFrame(get_user_input(mean_stats, hof_mean_stats), index=["user"])
    user_stats_scaled = data_scaler.transform(user_stats)

    streamlit.write(f"{round(float(model.predict(user_stats_scaled))*100, 2)}%")

if __name__ == "__main__":
    main()