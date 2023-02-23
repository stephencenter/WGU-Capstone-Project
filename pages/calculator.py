import os
import time
import traceback
import pandas
import tensorflow
import streamlit
import sklearn.model_selection
from tensorflow import keras

# This is the folder where our AI model will be stored so we don't have to retrain it every time the
# app is launched
model_path = "tensorflow_model"

def load_data():
    # Load the training dataset from its csv file and set its index as the player_id column
    training_dataframe = pandas.read_csv('training_data.csv')
    training_dataframe = training_dataframe.set_index('player_id')

    # training_x contains all of the data for each player in the training set including runs, at bats, etc
    # training_y is a key that tells us whether each player is in the hall of fame or not
    training_x = training_dataframe.drop('in_hall_of_fame', axis=1)
    training_y = training_dataframe['in_hall_of_fame']

    return training_x, training_y

def prepare_data(training_x, training_y):
    # We split our training data and labels into two groups, one for training and one for testing
    # This is done at a ratio of 4 training samples to 1 testing sample
    train_data, test_data, train_labels, test_labels = sklearn.model_selection.train_test_split(training_x, training_y, test_size=0.2, random_state=256)

    # The data scaler accounts for the fact that the magnitudes of our data are not all in the same ballpark
    # For example, players always have batting averages between 0 and 1, but their WAR could be any number
    # This data scaler adjusts all our values to the same -1 to 1 scale so they can be interpreted more easily by the
    # model
    data_scaler = sklearn.preprocessing.StandardScaler()
    train_data_scaled = data_scaler.fit_transform(train_data)
    test_data_scaled = data_scaler.transform(test_data)

    return train_data_scaled, train_labels, test_data_scaled, test_labels, data_scaler

def create_model():
    # Initialize a blank model with three layers
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

def train_model(model, train_data_scaled, train_labels):
    # Now we train the model to recognize hall of fame players using our training data
    model.fit(train_data_scaled, train_labels, epochs=100)

    return model

def get_user_input():
    # We have streamlit create a three-column layout for this page and put
    # five input boxes in each one. This way the user can see all the input
    # boxes at once on a normal 1080p monitor
    column_1, column_2, column_3 = streamlit.columns(3)

    # We use "with" to place these number inputs into our columns. The streamlit library will
    # collect the input from the boxes when the user types
    with column_1:
        war = streamlit.number_input("Wins Above Replacement (WAR)", value=0.0, min_value=-10.0, step=0.1, format="%.1f")
        batter_average = streamlit.number_input("Batting Average (BA)", min_value=0.0, max_value=1.0, step=0.001, format="%.3f")
        batter_ops = streamlit.number_input("On-base Plus Slugging (OPS)", min_value=0.0, max_value=5.0, step=0.001, format="%.3f")
        pitcher_losses = streamlit.number_input("Losses as pitcher (L)", min_value=0, step=1)
        pitcher_strikeouts = streamlit.number_input("Strikeouts (SO)", min_value=0, step=1)

    with column_2:
        batter_atbats = streamlit.number_input("At bats (AB)", min_value=0, step=1)
        batter_runs = streamlit.number_input("Runs (R)", min_value=0, step=1)
        pitcher_era = streamlit.number_input("Earned Run Average (ERA)", min_value=0.0, step=0.01, format="%.2f")
        pitcher_saves = streamlit.number_input("Saves (SV)", min_value=0, step=1)
        pitcher_whip = streamlit.number_input("Walks + Hits per Inning Pitched (WHIP)", min_value=0.0, step=0.001, format="%.3f")

    with column_3:
        batter_homeruns = streamlit.number_input("Home runs (HR)", min_value=0, step=1)
        batter_rbi = streamlit.number_input("Runs Batted In (RBI)", min_value=0, step=1)
        pitcher_wins = streamlit.number_input("Wins as pitcher (W)", min_value=0, step=1)
        pitcher_innings = streamlit.number_input("Innings pitched (IP)", min_value=0.0, step=0.1, format="%.1f")
        allstar_apps = streamlit.number_input("All-Star Game Appearances", min_value=0, step=1)

    # Return the values the user input into the boxes
    # We return it as a dictionary so we can convert it into a dataframe on the other side
    # The values have to be in this order because it's the same order as the training data
    return {
        "batter_atbats": batter_atbats,
        "batter_homeruns": batter_homeruns,
        "batter_ops": batter_ops,
        "batter_runs": batter_runs,
        "batter_rbi": batter_rbi,
        "batter_average": batter_average,
        "pitcher_innings": pitcher_innings,
        "pitcher_wins": pitcher_wins,
        "pitcher_losses": pitcher_losses,
        "pitcher_era": pitcher_era,
        "pitcher_whip": pitcher_whip,
        "pitcher_saves": pitcher_saves,
        "pitcher_strikeouts": pitcher_strikeouts,
        "war": war,
        "allstar_apps": allstar_apps
    }

def main():
    # We use the same tensorflow seed every time to avoid variation if the model needs to be regenerated
    tensorflow.random.set_seed(128)

    streamlit.title("Hall of Fame Calculator")
    streamlit.write("Input a player's career stats and an AI will say whether this player should be elected to the Hall of Fame")

    # Loading and preparing the data, model, etc. can take a long time, so we store
    # those things in streamlit's session state so we can quickly retrieve them later.
    # Otherwise we'd have to load everything every time we open the page
    if all(key in streamlit.session_state for key in ['loaded_model', 'data_scaler', 'model_eval']):
        model = streamlit.session_state['loaded_model']
        data_scaler = streamlit.session_state['data_scaler']
        model_evaluation = streamlit.session_state['model_eval']

    else:
        # This spinner will be visible until the code inside is done running
        with streamlit.spinner("Preparing AI..."):
            # Load and prepare the training data
            training_x, training_y = load_data()
            train_data, train_labels, test_data, test_labels, data_scaler = prepare_data(training_x, training_y)

            # If the model exists we load it from file, if it doesn't then we train a new one
            model = create_model()
            if os.path.exists(model_path):
                model = keras.models.load_model(model_path)

            else:
                model = train_model(model, train_data, train_labels)
                model.save(model_path)

            model_evaluation = model.evaluate(test_data, test_labels)

            # All of these variables are saved to session state as mentioned earlier
            streamlit.session_state['loaded_model'] = model
            streamlit.session_state['data_scaler'] = data_scaler
            streamlit.session_state['model_eval'] = model_evaluation

    # Get the input from the input boxes and convert it to a scaled dataframe
    user_input = get_user_input()
    user_stats = pandas.DataFrame(user_input, index=["user"])
    user_stats_scaled = data_scaler.transform(user_stats)

    # This lambda function takes a float and converts it to a percentage with two decimal places
    # Ex: 0.682930 -> 68.29
    percentage = lambda val: round(float(val)*100, 2)

    # This spinner will be visible until the code inside is done running
    with streamlit.spinner("Calculating..."):
        # We ask the AI what the chance is of a player with the stats the user input being elected to the hall of fame
        hof_prediction = model.predict(user_stats_scaled)
        streamlit.write(f"Based on past data, the AI estimates a **{percentage(hof_prediction)}%** chance of this player being elected to the Hall of Fame.")

        # Based on the AI's prediction, we ask it to make a recommendation
        if hof_prediction < 0.5:
            streamlit.write(f"The AI recommends that this player should **NOT** be elected to the Baseball Hall of Fame")
        else:
            streamlit.write(f"The AI recommends that this player **SHOULD** be elected to the Baseball Hall of Fame")

    # Display the evaluation of the AI model
    with streamlit.expander("Model Evaluation"):
        streamlit.write(f"Accuracy: {percentage(model_evaluation[1])}%")
        streamlit.write(f"Precision: {percentage(model_evaluation[2])}%")
        streamlit.write(f"Recall: {percentage(model_evaluation[3])}%")
        streamlit.write(f"Loss: {percentage(model_evaluation[0])}%")

if __name__ == "__main__":
    try:
        main()

    # If an error occurs during program execution, we log the error to a file
    except Exception as ex:
        log_dir = 'Error Logs'
        log_path = f"{log_dir}/{time.strftime('%Y-%m-%d_%H-%M-%S')}.txt"

        # Make the error log folder if it doesn't exist already
        try:
            os.makedirs(log_dir)
        except FileExistsError:
            pass

        # Write the error message to the log file
        with open(log_path, mode='w') as f:
            f.write(traceback.format_exc())

        # Raise the exception that was caught
        raise