import pandas
import streamlit
import plotly.express as express

def load_data():
    player_dataframe = pandas.read_csv('player_data.csv')
    player_dataframe = player_dataframe.set_index('player_id')

    progress_dataframe = pandas.read_csv('hof_progression.csv')

    return player_dataframe, progress_dataframe

def calculate_averages(player_dataframe : pandas.DataFrame):
    all_mean_data = {key: [] for key in player_dataframe.keys()}
    eligible_mean_data = {key: [] for key in player_dataframe.keys()}
    hof_mean_data = {key: [] for key in player_dataframe.keys()}

    # Players who have a zero will be ignored in calculating the averages for these stats.
    # This is important when averaging stats for pitching, as many batters (even HOF batters) will
    # go their entire career without pitching a single inning, dragging the averages further down than they
    # should be. This is especially relevant for Losses, ERA, and WHIP where lower is better, meaning that
    # players who've never pitched an inning will make the averages for those stats look much better than
    # they should be
    ignore_zeros = ['pitcher_innings', 'pitcher_wins', 'pitcher_losses', 'pitcher_era', 'pitcher_whip', 'pitcher_saves', 'pitcher_strikeouts']

    for player in player_dataframe.iterrows():
        player_data = player[1]

        for stat in player_data.keys():
            value = player_data[stat]
            if not isinstance(value, str) and not (value == 0 and stat in ignore_zeros):
                all_mean_data[stat].append(value)

                if player_data["num_seasons"] >= 10:
                    eligible_mean_data[stat].append(value)

                if player_data["in_hall_of_fame"]:
                    hof_mean_data[stat].append(value)

    for dictionary in [all_mean_data, eligible_mean_data, hof_mean_data]:
        for key in list(dictionary):
            try:
                dictionary[key] = sum(dictionary[key]) / len(dictionary[key])
            except ZeroDivisionError:
                del dictionary[key]

        dictionary['pitcher_winloss'] = dictionary['pitcher_wins']/dictionary['pitcher_losses']

    all_mean_df = pandas.DataFrame(all_mean_data, index=["Average (All)"])
    eligible_mean_df = pandas.DataFrame(eligible_mean_data, index=["Average (Eligible)"])
    hof_mean_df = pandas.DataFrame(hof_mean_data, index=["Average (HOF)"])

    return all_mean_df, eligible_mean_df, hof_mean_df

def display_player_stat_charts(all_mean_stats, eligible_mean_stats, hof_mean_stats):
    stat_list = [
        ('war', "Wins Above Replacement (WAR)", "WAR"),
        ('batter_atbats', "At bats (AB)", "AB"),
        ('batter_average', "Batting Average (BA)", "AVG"),
        ('batter_obp', "On-base Percentage (OBP)", "OBP"),
        ('batter_slugging', "Slugging Average (SLG)", "SLG"),
        ('pitcher_innings', "Innings Pitched (IP)", "IP"),
        ('pitcher_era', "Earned Run Average (ERA)", "ERA"),
        ('pitcher_whip', "Walks + Hits per Inning Pitched (WHIP)", "WHIP"),
        ('pitcher_winloss', "Win/Loss Ratio as Pitcher", "W-L%"),
        ('allstar_apps', "All-Star Game Appearances", "All-Star")
    ]

    tab_list = streamlit.tabs([x[2] for x in stat_list])

    for index, tab in enumerate(tab_list):
        with tab:
            stat = stat_list[index][0]
            stat_name = stat_list[index][1]
            stat_chart = express.bar({"All": all_mean_stats[stat], "Eligible": eligible_mean_stats[stat], "HOF": hof_mean_stats[stat]},
                                     labels={'variable': 'Legend', 'value': stat_name, 'index': ''})
            streamlit.plotly_chart(stat_chart)

def display_player_hand_charts(player_dataframe):
    tab_1, tab_2, tab_3 = streamlit.tabs(["Batting Hand", "Throwing Hand", "Combinations"])
    with tab_1:
        batting_hand_data = player_dataframe['hand_batting'].tolist()
        batting_hand_dict = {"names": ["Left", "Right"],
                             "values": [batting_hand_data.count("L"), batting_hand_data.count("R")]}
        batting_hand_chart = express.pie(batting_hand_dict, values="values", names='names')

        streamlit.write("Right vs Left Hand for Batting")
        streamlit.plotly_chart(batting_hand_chart)

    with tab_2:
        throwing_hand_data = player_dataframe['hand_throwing'].tolist()
        throwing_hand_dict = {"names": ["Left", "Right"],
                              "values": [throwing_hand_data.count("L"), throwing_hand_data.count("R")]}
        throwing_hand_chart = express.pie(throwing_hand_dict, values="values", names='names')
        streamlit.write("Right vs Left Hand for Throwing")
        streamlit.plotly_chart(throwing_hand_chart)

    with tab_3:
        both_left = 0
        both_right = 0
        bat_left_throw_right = 0
        bat_right_throw_left = 0
        for player in player_dataframe.iterrows():
            bat_hand = player[1]['hand_batting']
            throw_hand = player[1]['hand_throwing']

            if bat_hand == "L" and throw_hand == "L":
                both_left += 1
            elif bat_hand == "R" and throw_hand == "R":
                both_right += 1
            elif bat_hand == "L" and throw_hand == "R":
                bat_left_throw_right += 1
            elif bat_hand == "R" and throw_hand == "L":
                bat_right_throw_left += 1

        player_hand_dict = {"names": ["Both L", "Both R", "Bat L, Throw R", "Bat R, Throw L"],
                            "values": [both_left, both_right, bat_left_throw_right, bat_right_throw_left]}

        player_hand_chart = express.pie(player_hand_dict, values="values", names='names')
        streamlit.write("Batting and Throwing Hand Combinations")
        streamlit.plotly_chart(player_hand_chart)

def display_hof_progression_charts(progress_df):
    progress_chart = express.line(progress_df, x='Year', y=progress_df.columns[1:3], labels={'variable':'Legend', 'value':'Number of Inductees'})
    streamlit.plotly_chart(progress_chart)

def main():
    player_df, progress_df = load_data()
    all_mean_df, eligible_mean_df, hof_mean_df = calculate_averages(player_df)

    streamlit.subheader("Average Stat Comparisons")
    display_player_stat_charts(all_mean_df, eligible_mean_df, hof_mean_df)

    streamlit.subheader("Hall of Fame Inductees Over Time")
    display_hof_progression_charts(progress_df)

    streamlit.subheader("Primary Hands for Batting and Throwing")
    display_player_hand_charts(player_df)

if __name__ == "__main__":
    main()