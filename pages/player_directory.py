import pandas
import streamlit

def load_data():
    player_dataframe = pandas.read_csv('player_data.csv')

    return player_dataframe

def find_matching_players(input_string : str , player_dataframe):
    results = []
    for player in player_dataframe.iterrows():
        if input_string in player[1]["player_id"].lower() or input_string in player[1]["player_name"].lower():
            player_dict = player[1].to_dict()
            results.append(player_dict)

    return pandas.DataFrame(results)

def find_player_by_id(player_id : str, player_dataframe):
    for player in player_dataframe.iterrows():
        if player[1]['player_id'] == player_id:
            return player[1]

    return None

def display_search_results(search_results, user_search):
    search_limit = 50

    if len(search_results) > search_limit:
        streamlit.subheader(f"Displaying first {search_limit} of {len(search_results)} matches for '{user_search}'")

    else:
        streamlit.subheader(f"Found {len(search_results)} matches for '{user_search}'")

    column_format = (2, 1, 1, 1, 1)
    columns = streamlit.columns(column_format)
    col_headers = ["Name", "BBref ID", "MLB Debut", "HOF?", "Player Page"]
    for col, header in zip(columns, col_headers):
        col.markdown(f"**{header}**")

    counter = 0
    for result in search_results.iterrows():
        counter += 1
        if counter > search_limit:
            break

        col1, col2, col3, col4, col5 = streamlit.columns(column_format)
        col1.write(result[1]['player_name'])
        col2.write(result[1]['player_id'])
        col3.write(result[1]['debut_date'])
        col4.write("Yes" if result[1]['in_hall_of_fame'] else "No")
        button_placeholder = col5.empty()
        button_placeholder.button("View", key=result[1]['player_id'], on_click=set_selected_player, args=[result[1]['player_id']])

def display_player_info(sel_player):
    streamlit.title(f"{sel_player['player_name']} ({streamlit.session_state['selected_player']})")
    streamlit.subheader(f"General Player Information")

    info_column_1, info_column_2 = streamlit.columns(2)
    with info_column_1:
        streamlit.write(f"Player Name: {sel_player['player_name']}")
        streamlit.write(f"Birthdate: {sel_player['birth_date']}")
        streamlit.write(f"Height: {sel_player['height']}")
        streamlit.write(f"Batting Hand: {sel_player['hand_batting']}")
        streamlit.write(f"MLB Debut Date: {sel_player['debut_date']}")

    with info_column_2:
        streamlit.write(f"BBref ID: {streamlit.session_state['selected_player']}")
        streamlit.write(f"Birthplace: {sel_player['birth_place']}")
        streamlit.write(f"Weight: {sel_player['weight']}")
        streamlit.write(f"Throwing Hand: {sel_player['hand_throwing']}")
        streamlit.write(f"In Hall of Fame? {'Yes' if sel_player['in_hall_of_fame'] else 'No'}")

    streamlit.subheader(f"Player Career Stats")

    stats_column_1, stats_column_2 = streamlit.columns(2)
    with stats_column_1:
        streamlit.write(f"At bats (AB): {sel_player['batter_atbats']}")
        streamlit.write(f"Hits (H): {sel_player['batter_hits']}")
        streamlit.write(f"Runs (R): {sel_player['batter_runs']}")
        streamlit.write(f"Home runs (HR): {sel_player['batter_homeruns']}")
        streamlit.write(f"On-base Percentage (OBP): {sel_player['batter_obp']}")
        streamlit.write(f"Slugging Average (SLG): {sel_player['batter_slugging']}")
        streamlit.write(f"Runs Batted In (RBI): {sel_player['batter_rbi']}")
        streamlit.write(f"Batting Average: {sel_player['batter_average']}")
        streamlit.write(f"Seasons played: {sel_player['num_seasons']}")
        streamlit.write(f"All-Star Games: {sel_player['allstar_apps']}")

    with stats_column_2:
        streamlit.write(f"Innings Pitched (IP): {sel_player['pitcher_innings']}")
        streamlit.write(f"Wins as Pitcher (W): {sel_player['pitcher_wins']}")
        streamlit.write(f"Losses as Pitcher (L): {sel_player['pitcher_losses']}")
        streamlit.write(f"Earned Run Average (ERA): {sel_player['pitcher_era']}")
        streamlit.write(f"Wins + Hits per Inning Pitched (WHIP): {sel_player['pitcher_whip']}")
        streamlit.write(f"Saves (SV): {sel_player['pitcher_saves']}")
        streamlit.write(f"Strikeouts (SO): {sel_player['pitcher_strikeouts']}")
        streamlit.write(f"Wins Above Replacement (WAR): {sel_player['war']}")
        streamlit.write(f"Games played: {sel_player['num_games']}")

    streamlit.caption("Stats current up to 2021")
    streamlit.caption("Data sourced from Sean Lahman’s Baseball Database")
    streamlit.caption("WAR calculation sourced from baseball-database.com")

def set_selected_player(player_id):
    streamlit.session_state['selected_player'] = player_id

def main():
    if 'selected_player' not in streamlit.session_state:
        streamlit.session_state['selected_player'] = None

    player_dataframe = load_data()

    if streamlit.session_state['selected_player'] is not None:
        streamlit.button("Back to player directory", key='top_back', on_click=set_selected_player, args=[None])
        sel_player = find_player_by_id(streamlit.session_state['selected_player'], player_dataframe)
        display_player_info(sel_player)

    else:
        streamlit.title("MLB Player Directory")
        user_search = streamlit.text_input("Type in a player's name or BBref ID").lower().strip()

        if user_search:
            search_results = find_matching_players(user_search, player_dataframe)
            display_search_results(search_results, user_search)

if __name__ == "__main__":
    main()