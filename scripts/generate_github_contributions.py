from dotenv import load_dotenv
import os
import requests
import pandas as pd
import plotly.express as px
import webbrowser

# Load environment variables from .env file
load_dotenv()
token = os.getenv("GITHUB_TOKEN")

# Define your GitHub username
username = "sminerport"

# GitHub API endpoint
url = "https://api.github.com/graphql"

# GraphQL query
query = """
{
  user(login: "sminerport") {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

# Headers for the request
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Make the request
response = requests.post(url, json={"query": query}, headers=headers)

# Process the response
data = response.json()
weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

# Flatten the data
contributions = []
for week in weeks:
    for day in week["contributionDays"]:
        contributions.append(
            {"date": day["date"], "contributionCount": day["contributionCount"]}
        )

# Create a DataFrame
df = pd.DataFrame(contributions)

# Convert date column to datetime
df["date"] = pd.to_datetime(df["date"])


# Create Plotly bar chart function
def create_plot(df, theme, html_filename, png_filename, annotation_color):
    fig = px.bar(
        df,
        x="date",
        y="contributionCount",
        title=f"GitHub Contributions in 2024 - {theme} Theme",
    )

    # Customize the layout
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Contributions",
        title_font=dict(size=24),
        xaxis=dict(title_font=dict(size=18), tickfont=dict(size=14)),
        yaxis=dict(title_font=dict(size=18), tickfont=dict(size=14)),
        template=theme,
    )

    # Adding Annotations
    annotations = [
        dict(
            x="2024-03-18",  # Example date
            y=14,
            xref="x",
            yref="y",
            text="Significant Contribution",
            showarrow=True,
            arrowhead=2,
            arrowsize=2,
            arrowwidth=2,
            ax=80,  # Adjusted for pointing up and to the right
            ay=-40,  # Adjusted for pointing up and to the right
            font=dict(size=16, color=annotation_color),  # Enlarge the text
            align="center",
            arrowcolor="red",
        )
    ]
    fig.update_layout(annotations=annotations)

    # Save the figure as an HTML file
    fig.write_html(html_filename)

    # Save the figure as a PNG file
    fig.write_image(png_filename)

    # Optionally, open the HTML file in the default web browser
    webbrowser.open(f"file://{os.path.abspath(html_filename)}")

    # Show the figure
    # fig.show()


# Generate the dark version
create_plot(df, "plotly_dark", "docs/contributions_plot_dark.html", "docs/contributions_plot_dark.png", "white")

# Generate the light version
create_plot(df, "plotly", "docs/contributions_plot_light.html", "docs/contributions_plot_light.png", "black")
