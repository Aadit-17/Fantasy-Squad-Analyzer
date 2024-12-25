import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Function to scrape FPL data for a specific team using team_id
def get_fpl_team_data(team_id):
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/history/"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Failed to retrieve team data. Please check the team ID.")
        return None
    return response.json()

# Function to get player's points data from a team's performance in a specific gameweek
def get_player_data(team_id, gameweek):
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gameweek}/picks/"
    response = requests.get(url)
    if response.status_code != 200:
        st.error(f"Failed to retrieve player data for gameweek {gameweek}.")
        return None
    return response.json()

# Function to visualize the trend in points for the last 5 gameweeks
def plot_points_trend(team_data):
    gameweeks = []
    points = []
    
    # Iterate through history to get the latest gameweeks with points > 0
    for item in team_data['current']:
        if item['points'] > 0:
            gameweeks.append(item['event'])
            points.append(item['points'])
    
    # Take the last 5 gameweeks
    gameweeks = gameweeks[-5:]
    points = points[-5:]

    # Plotting the points trend
    plt.figure(figsize=(10, 6))
    plt.plot(gameweeks, points, marker='o', color='b', label='Points')
    plt.xlabel('Gameweek')
    plt.ylabel('Points')
    plt.title('Points Trend Over Last 5 Gameweeks')
    plt.xticks(gameweeks)
    plt.legend()
    plt.grid(True)
    st.pyplot(plt)

# Function to map element_type (position_id) to human-readable position
def get_position_from_id(position_id):
    position_map = {
        1: 'GK',  # Goalkeeper
        2: 'DEF', # Defender
        3: 'MID', # Midfielder
        4: 'FWD'  # Forward
    }
    return position_map.get(position_id, 'Unknown')

# Function to get player's data
def get_all_players():
    players_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    players_response = requests.get(players_url)
    
    if players_response.status_code != 200:
        st.error("Failed to retrieve player data.")
        return None
    
    players_data = players_response.json()
    
    # Create a DataFrame for all players
    player_info = []
    
    for player in players_data['elements']:
        player_info.append({
            'player_id': player['id'],
            'player_name': player['web_name'],
            'form': float(player['form']),  # Ensure form is a float
            'now_cost': player['now_cost'],
            'selected_by_percent': float(player['selected_by_percent']),
            'element_type': (player['element_type'])
        })
    
    return pd.DataFrame(player_info)

# Function to get recommended players based on the selected player's position
def recommend_players_by_position(selected_player_name, player_data, same_price_checkbox):
    # Get the selected player's details
    selected_player = player_data[player_data['player_name'] == selected_player_name].iloc[0]

    # Get the position of the selected player
    selected_position = selected_player['element_type']

    # Filter available players by position
    available_players = player_data[player_data['element_type'] == selected_position]

    # If the same price checkbox is selected, filter players with the same price or less
    if same_price_checkbox:
        available_players = available_players[available_players['now_cost'] <= selected_player['now_cost']]

    # Sort by form (descending) and selected_by_percent (ascending)
    recommended_players = available_players.sort_values(by=['form', 'selected_by_percent'], ascending=[False, True]).head(3)
    recommended_players['position'] = get_position_from_id(recommended_players['element_type'])

    return recommended_players[['player_name', 'form', 'now_cost', 'selected_by_percent', 'position']]

def main():
    st.title("Fantasy Premier League Team Analyzer")
    
    # Input field for the user's FPL team ID
    team_id = st.text_input("Enter your FPL Team ID:", "")

    if team_id:
        # Fetch team data
        team_data = get_fpl_team_data(team_id)
        if team_data:
            st.header(f"Team Performance for Team ID: {team_id}")
            
            # Determine the current gameweek based on the latest entry with points > 0
            latest_gameweek = max(item['event'] for item in team_data['current'] if item['points'] > 0)
            st.subheader(f"Current Gameweek: {latest_gameweek}")

            # Show points trend for the last 5 gameweeks
            st.subheader("Points Trend (Last 5 Gameweeks)")
            plot_points_trend(team_data)

            # Get player's picks for the current gameweek
            team_picks = get_player_data(team_id, latest_gameweek)
            if team_picks is not None:
                # Get all players data for analysis
                player_data = get_all_players()
                if player_data is not None:
                    team_player_names = [player['player_name'] for player in team_picks['picks']]

                    # Display the players' names for selection
                    st.subheader("Select a Player to Replace")

                    selected_player_name = st.selectbox("Select a Player:", [player_name for player_name in player_data['player_name'] if player_name in team_player_names])
                    same_price_checkbox = st.checkbox("Same Price")

                    if selected_player_name:
                        # Get recommended players based on the selected player
                        recommended_players = recommend_players_by_position(
                            selected_player_name, player_data, same_price_checkbox
                        )

                        # Display the recommended players
                        st.subheader("Recommended Transfers")
                        st.dataframe(recommended_players, hide_index=True)
                else:
                    st.error("Unable to fetch player data.")
            else:
                st.error("Unable to fetch your team's player data.")
        else:
            st.error("Unable to fetch team data. Please check your Team ID.")
    else:
        st.info("Enter your FPL Team ID to analyze your team.")

if __name__ == "__main__":
    main()
