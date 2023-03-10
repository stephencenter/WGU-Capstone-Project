import time
import os
import traceback
import pandas
import streamlit
import plotly.express as express

def load_data():
    # Load the data from these csv files and store them in dataframes
    player_dataframe = pandas.read_csv('player_data.csv')
    player_dataframe = player_dataframe.set_index('player_id')
    progress_dataframe = pandas.read_csv('hof_progression.csv')

    return player_dataframe, progress_dataframe

def calculate_averages(player_dataframe : pandas.DataFrame):
    # 'All' refers to every player who has ever played in the MLB
    all_mean_data = {key: [] for key in player_dataframe.keys()}

    # 'Eligible' refers to every player who has played at least 10 seasons in the MLB
    eligible_mean_data = {key: [] for key in player_dataframe.keys()}

    # 'HOF' refers to every player who has been inducted into the baseball hall of fame
    hof_mean_data = {key: [] for key in player_dataframe.keys()}

    # Players who have never pitched an inning will be ignored in calculating the averages for these stats.
    # This is important when averaging stats for pitching, as many batters (even HOF batters) will
    # go their entire career without pitching a single inning, dragging the averages further down than they
    # should be. This is especially relevant for ERA and WHIP where lower is better, meaning that
    # players who've never pitched an inning will make the averages for those stats look much better than
    # they should be
    ignore_zeros = ['pitcher_innings', 'pitcher_era', 'pitcher_whip', 'pitcher_wins', 'pitcher_losses', 'pitcher_saves', 'pitcher_strikeouts']

    # Iterate through every player in the player dataframe
    for player in player_dataframe.iterrows():
        player_data = player[1]

        # Iterate through each stat for the current player
        for stat in player_data.keys():
            value = player_data[stat]

            # We ignore certain stats if the player in question hasn't pitched an inning
            if stat in ignore_zeros and player_data['pitcher_innings'] == 0:
                continue

            # If the value of the stat is a string, that means it's something that can't be averaged like
            # a name or birth location. If it isn't a string, then we add the value to the proper dictionary
            # assuming the requirement is met
            if not isinstance(value, str):
                all_mean_data[stat].append(value)

                if player_data["in_hall_of_fame"]:
                    hof_mean_data[stat].append(value)

                if player_data["num_seasons"] >= 10:
                    eligible_mean_data[stat].append(value)

    # Iterate through each of the three dictionaries we've created
    for dictionary in [all_mean_data, eligible_mean_data, hof_mean_data]:
        # Each key in our dictionary corresponds to a list of values
        # We need to take the average of these lists and set the keys equal to that
        # Ex. 'batter_homeruns': [0, 15, 32, 8, 100, 7] -> 'batter_homeruns': 27
        for key in list(dictionary):
            try:
                dictionary[key] = sum(dictionary[key]) / len(dictionary[key])
            except ZeroDivisionError:
                del dictionary[key]

        # Win-loss percentage is a stat that isn't recorded in the datasheet, but it's very easy to calculate here
        dictionary['pitcher_winloss'] = dictionary['pitcher_wins']/(dictionary['pitcher_wins'] + dictionary['pitcher_losses'])

    # Convert our dictionaries to dataframes and return them
    all_mean_df = pandas.DataFrame(all_mean_data, index=["Average (All)"])
    eligible_mean_df = pandas.DataFrame(eligible_mean_data, index=["Average (Eligible)"])
    hof_mean_df = pandas.DataFrame(hof_mean_data, index=["Average (HOF)"])

    return all_mean_df, eligible_mean_df, hof_mean_df

def display_player_stat_charts(all_mean_stats, eligible_mean_stats, hof_mean_stats):
    # This is a list of every stat that we'll be displaying a chart for
    # Each item in the list is a tuple with 4 items
    # Item 0 is the key for the dataframes, item 1 is the label for the chart's y axis,
    # item 2 is the text that will mark the tab for the stat, and item 3 is a description of
    # the stat
    stat_list = [
        ('war', "Wins Above Replacement (WAR)", "WAR",
"""Wins Above Replacement (WAR) is an estimate of how many games were won by a player's team that would have been lost 
had that player been swapped out for a 'typical' player. It is a subjective statistic with no universal method of
calculation. The dataset for this project uses the player's WAR as calculated by baseball-reference.com.
\nA higher WAR stat is better."""),

        ('batter_atbats', "At bats (AB)", "AB",
"""At bats (AB) is the number of times a player stepped up to the home plate to bat and achieved either a hit
or an out, not including sacrifice hits or sacrifice flies. Plate appearances ending in a walk or hit-by-pitch
are also not considered at bats."""),

        ('batter_homeruns', "Home runs (HR)", "HR",
"""Home Runs (HR) is the number of times a player hit the ball and then managed to round all four bases in one play."""),

        ('batter_average', "Batting Average (BA)", "AVG",
"""Batting Average (AVG) is a player's ratio of Hits to At Bats.
\nA higher batting average is better."""),

        ('batter_obp', "On-base Percentage (OBP)", "OBP",
"""On-base Percentage (OBP) is how frequently a player reaches base after stepping up to bat. This includes walks
and hit-by-pitches.
\nA higher on-base percentage is better."""),

        ('batter_slugging', "Slugging Average (SLG)", "SLG",
"""Slugging Average (SLG), also called 'Slugging Percentage', is the total number of bases ran divided by the total
number of at bats. Total bases is calculated as (Singles + 2\*Doubles + 3\*Triples + 4\*Home Runs).
\nA higher slugging average is better."""),

        ('pitcher_innings', "Innings Pitched (IP)", "IP",
"""Innings Pitched (IP) is the total number of innings completed by a pitcher. As three outs ends an inning, 
innings pitched is equal to one third the total number of outs that occurred while the pitcher was on the mound.
\nOnly players who have pitched at least one inning were used to calculate these averages."""),

        ('pitcher_era', "Earned Run Average (ERA)", "ERA",
"""Earned Run Average (ERA) is the ratio of opponent runs allowed by a pitcher to the number of 9-inning games that
pitcher has pitched.
\nA lower earned run average is better. Only players who have pitched at least one inning were used to calculate these averages."""),

        ('pitcher_whip', "Walks + Hits per Inning Pitched (WHIP)", "WHIP",
"""Walks + Hits per Inning Pitched (WHIP) is the number of walks and hits a pitcher allowed divided by the number of
innings the player pitched.
\nA lower WHIP is better. Only players who have pitched at least one inning were used to calculate these averages."""),

        ('pitcher_winloss', "Win/Loss Percentage as Pitcher", "W-L%",
"""Win-Loss Percentage as Pitcher (W-L%) is the ratio of games won by a pitcher to games pitched by that pitcher.
A win-loss ratio above 0.5 means the pitcher wins more than they lose, and below 0.5 means they lose more than they win.
\nA higher W-L% is better. Only players who have pitched at least one inning were used to calculate these averages."""),

        ('pitcher_strikeouts', "Strikeouts (SO)", "SO",
"""Strikeouts (SO) is the number of times a pitcher threw three strikes in a single opponent's at bat, 
causing an out.
\nOnly players who have pitched at least one inning were used to calculate these averages."""),

        ('allstar_apps', "All-Star Game Appearances", "All-Star",
"""All-Star Game Appearances is the number of times a player was selected for the MLB's annual All-Star Game's roster.""")
    ]

    # Create a list of tabs for our stat charts. Each tab will correspond to one stat,
    # and will contain a chart and a description of what the stat means
    tab_list = streamlit.tabs([x[2] for x in stat_list])

    # This is the explanation for how the charts work
    chart_explanation = """
'All' refers to the average value across all 20370 players in the dataset.
\n'Eligible' refers to the average value across the 4137 players who have played the minimum 10 seasons required to 
become eligible for election to the Baseball Hall of Fame
\n'HOF' refers to the average value across the 271 players who have actually been elected to the baseball hall of 
fame."""

    # Iterate through the list of tabs while keeping track of which index we're at
    for index, tab in enumerate(tab_list):
        with tab:
            stat = stat_list[index][0]
            stat_name = stat_list[index][1]
            stat_abbreviation = stat_list[index][2]
            stat_desc = stat_list[index][3]

            # The text in this expander is hidden unless the user clicks the expander
            with streamlit.expander(f"What does '{stat_abbreviation}' mean?"):
                streamlit.write(stat_desc)

            # Create a bar chart and display it with streamlit
            stat_chart = express.bar({"All": all_mean_stats[stat], "Eligible": eligible_mean_stats[stat], "HOF": hof_mean_stats[stat]},
                                     labels={'variable': 'Legend', 'value': stat_name, 'index': ''})
            streamlit.plotly_chart(stat_chart)

            # Display the chart explanation
            streamlit.write(chart_explanation)

def display_hof_progression_charts(progress_df):
    streamlit.write("""
Since its formation in 1936, the Baseball Writers' Association of America (BBWAA) has conducted yearly elections
to determine which players should be inducted into the National Baseball Hall of Fame. Over the years a total of
271 players have been inducted into the Hall of Fame, and they represent what the BBWAA considers the best of
the best.""")

    # Create a line chart from the progress dataframe and display it with streamlit
    progress_chart = express.line(progress_df, x='Year', y=progress_df.columns[1:3], labels={'variable':'Legend', 'value':'Number of Inductees'})
    streamlit.plotly_chart(progress_chart)

def display_player_hand_charts(player_dataframe):
    # These dictionaries are running totals of how many people use each hand to play baseball,
    # as well as batting and throwing hand combinations
    individual = { 'bat_left': 0, 'bat_right': 0, 'throw_left': 0, 'throw_right': 0 }
    combinations = { 'both_left': 0, 'both_right': 0, 'b_left_t_right': 0, 'b_right_t_left': 0 }

    # Iterate through each player in the dataframe and tally up which hands they use for each task
    for player in player_dataframe.iterrows():
        bat_hand = player[1]['hand_batting']
        throw_hand = player[1]['hand_throwing']

        if bat_hand == "L" and throw_hand == "L":
            individual['bat_left'] += 1
            individual['throw_left'] += 1
            combinations['both_left'] += 1

        elif bat_hand == "R" and throw_hand == "R":
            individual['bat_right'] += 1
            individual['throw_right'] += 1
            combinations['both_right'] += 1

        elif bat_hand == "L" and throw_hand == "R":
            individual['bat_left'] += 1
            individual['throw_right'] += 1
            combinations['b_left_t_right'] += 1

        elif bat_hand == "R" and throw_hand == "L":
            individual['bat_right'] += 1
            individual['throw_left'] += 1
            combinations['b_right_t_left'] += 1

    # We create three different charts: one for batting, one for throwing, and one for combinations of the two
    tab_1, tab_2, tab_3 = streamlit.tabs(["Batting Hand", "Throwing Hand", "Combinations"])
    with tab_1:
        bat_hand_dict = {"names": ["Left", "Right"], "values": [individual['bat_left'], individual['bat_right']]}
        bat_hand_chart = express.pie(bat_hand_dict, values="values", names='names')
        streamlit.write("Right vs Left Hand for Batting")
        streamlit.plotly_chart(bat_hand_chart)

    with tab_2:
        throw_hand_dict = {"names": ["Left", "Right"], "values": [individual['throw_left'], individual['throw_right']]}
        throw_hand_chart = express.pie(throw_hand_dict, values="values", names='names')
        streamlit.write("Right vs Left Hand for Throwing")
        streamlit.plotly_chart(throw_hand_chart)

    with tab_3:
        player_hand_dict = {"names": ["Both L", "Both R", "Bat L, Throw R", "Bat R, Throw L"],
                            "values": [combinations['both_left'], combinations['both_right'],
                                       combinations['b_left_t_right'], combinations['b_right_t_left']]}
        player_hand_chart = express.pie(player_hand_dict, values="values", names='names')
        streamlit.write("Batting and Throwing Hand Combinations")
        streamlit.plotly_chart(player_hand_chart)

def main():
    streamlit.title("150 Years of MLB History Visualized")

    # Loading and preparing the data can take a long time, so we store those things in
    # streamlit's session state so we can quickly retrieve them later.
    # Otherwise we'd have to load everything every time we open the page
    if all(key in streamlit.session_state for key in ['averages', 'progress_df', 'player_df']):
        all_mean_df, eligible_mean_df, hof_mean_df = streamlit.session_state['averages']
        progress_df = streamlit.session_state['progress_df']
        player_df = streamlit.session_state['player_df']

    else:
        # This spinner will be visible until the code inside is done running
        with streamlit.spinner("Loading data..."):
            player_df, progress_df = load_data()
            all_mean_df, eligible_mean_df, hof_mean_df = calculate_averages(player_df)

            # All of these variables are saved to session state as mentioned earlier
            streamlit.session_state['averages'] = all_mean_df, eligible_mean_df, hof_mean_df
            streamlit.session_state['progress_df'] = progress_df
            streamlit.session_state['player_df'] = player_df

    streamlit.subheader("Average Stat Comparisons")
    display_player_stat_charts(all_mean_df, eligible_mean_df, hof_mean_df)

    streamlit.subheader("Hall of Fame Inductees Over Time")
    display_hof_progression_charts(progress_df)

    streamlit.subheader("Primary Hands for Batting and Throwing")
    display_player_hand_charts(player_df)

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