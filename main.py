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
        })
    
    return pd.DataFrame(player_info)

# Function to get best and worst performing players from the team's picks
def get_best_worst_from_team_picks(team_picks, player_data):
    # Extract player IDs from team picks
    player_ids = [pick['element'] for pick in team_picks['picks']]
    team_players = player_data[player_data['player_id'].isin(player_ids)]
    
    worst_players = team_players.nsmallest(7, 'form')
    best_players = team_players.nlargest(7, 'form')

    return worst_players[['player_name', 'form', 'now_cost']], best_players[['player_name', 'form', 'now_cost']]

# Function to get recommended transfers based on worst performers
def get_recommended_transfers(worst_players, player_data):
    total_worst_value = worst_players['now_cost'].sum()
    
    # Find better performing players within the budget and include differentials
    potential_transfers = player_data[
        (player_data['now_cost'] <= total_worst_value) & 
        (player_data['form'] > worst_players['form'].sum() / 7) &
        (player_data['selected_by_percent'] < 15)  # Change here to less than 15
    ].copy()

    # Sort potential transfers by form, descending
    recommended_transfers = potential_transfers.sort_values(by='form', ascending=False).head(7)

    return recommended_transfers[['player_name', 'form', 'now_cost', 'selected_by_percent']]

# Main Streamlit app logic
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
                    # Get best and worst performing players from the team's picks
                    worst_players, best_players = get_best_worst_from_team_picks(team_picks, player_data)

                    # Display the best performing players
                    st.subheader("Best Performing Players from Your Picks")
                    st.dataframe(best_players, hide_index=True)  # Hide index

                    # Display the worst performing players
                    st.subheader("Worst Performing Players from Your Picks")
                    st.dataframe(worst_players, hide_index=True)  # Hide index

                    # Get recommended transfers based on the 7 worst performers
                    recommended_transfers = get_recommended_transfers(worst_players, player_data)

                    # Display recommended transfers
                    st.subheader("Recommended Transfers (Differentials)")
                    st.dataframe(recommended_transfers, hide_index=True)  # Hide index

if __name__ == "__main__":
    main()