import os
import io
from playbook import load
from playbook import plays
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
import matplotlib.backends.backend_pdf
import matplotlib.pyplot as plt
import seaborn as sns

cwd = os.getcwd()
file_path_cfb = cwd

def calculate_report_criteria(current_datetime):
    df_cfb_reporting_schedule = load.sqlite_query_table('cfb_reporting_schedule')
    df_cfb_reporting_schedule['firstGameStart'] = pd.to_datetime(df_cfb_reporting_schedule['firstGameStart'])
    df_current_datetime = pd.to_datetime(current_datetime)
    #closest_date = df_cfb_reporting_schedule.loc[(df_cfb_reporting_schedule['firstGameStart'] - df_current_datetime).abs().idxmin(), 'firstGameStart']
    closest_idx_date = (df_cfb_reporting_schedule['firstGameStart'] - df_current_datetime).abs().idxmin()
    closest_row_date = df_cfb_reporting_schedule.loc[closest_idx_date]
    report_week = closest_row_date['week']
    report_year = closest_row_date['season']
    report_season_type = closest_row_date['seasonType']
    return report_year, report_week, report_season_type


def pdf_matchup_reports_old(reporting_year, reporting_week, report_season_type):
    print('Generating Reports for current week of the year')
    reporting_year = str(reporting_year)
    file_path_cfb_reports = cwd + '/reports/cfb/'
    file_path_cfb_reports_reporting_year = file_path_cfb_reports + str(reporting_year) + '/'
    file_path_cfb_reports_reporting_year_week_season_type = file_path_cfb_reports_reporting_year + str(report_season_type) + '/'
    file_path_cfb_reports_reporting_year_week = file_path_cfb_reports_reporting_year_week_season_type + 'Week_' + str(reporting_week) + '/'

    cfb_season_week_matchups = load.sqlite_query_table('cfb_reporting_season_week_matchups')
    cfb_all_data = load.sqlite_query_table('cfb_reporting_all_data')
    cfb_team_info = load.sqlite_query_table('cfb_reporting_team_info')
    cfb_summary = load.sqlite_query_table('cfb_reporting_summary')
    cfb_season_stats_by_season = load.sqlite_query_table('cfb_reporting_season_stats_by_season')

    df_cfb_for_reporting_game_matchup = cfb_season_week_matchups[cfb_season_week_matchups['season'].astype(str).str.contains(reporting_year)]
    df_cfb_for_reporting_game_matchup_reporting_week = df_cfb_for_reporting_game_matchup.loc[(df_cfb_for_reporting_game_matchup['week'] == int(reporting_week)) & (df_cfb_for_reporting_game_matchup['season_type'] == str(report_season_type))]
    cfb_all_data_reporting_year = cfb_all_data.loc[cfb_all_data['season'] == str(reporting_year)]

    for index, row in df_cfb_for_reporting_game_matchup_reporting_week.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        matchup = row['Game Matchup']
        df_home_team_all_data = cfb_all_data.loc[cfb_all_data['team'] == home_team]
        df_away_team_all_data = cfb_all_data.loc[cfb_all_data['team'] == away_team]
        home_team_color = cfb_team_info.loc[cfb_team_info['team'] == home_team, 'color'].iloc[0]
        away_team_color = cfb_team_info.loc[cfb_team_info['team'] == away_team, 'color'].iloc[0]

        df_matchup_home_away_all_data = pd.concat([df_home_team_all_data, df_away_team_all_data], ignore_index=True)
        df_matchup_home_away_all_data_current_season = df_matchup_home_away_all_data.loc[
            df_matchup_home_away_all_data['season'] == str(reporting_year)]

        df_cfb_summary_home_team = cfb_summary.loc[cfb_summary['team'] == (home_team)]
        df_cfb_summary_away_team = cfb_summary.loc[cfb_summary['team'] == (away_team)]
        df_cfb_summary_home_away_append = pd.concat([df_cfb_summary_home_team, df_cfb_summary_away_team], ignore_index=True).reset_index()

        df_cfb_season_stats_by_season_home_team = cfb_season_stats_by_season.loc[cfb_season_stats_by_season['team'] == (home_team)]
        df_cfb_season_stats_by_season_away_team = cfb_season_stats_by_season.loc[cfb_season_stats_by_season['team'] == (away_team)]
        df_cfb_season_stats_by_season_home_away_append = pd.concat([df_cfb_season_stats_by_season_home_team, df_cfb_season_stats_by_season_away_team], ignore_index=True)
        df_cfb_season_stats_by_season_home_away_append.sort_values(by=['season','team'], inplace=True, ascending=False)

        #Create DF for Matchup Summary
        df_matchup_home_away_all_data_sel_col = df_matchup_home_away_all_data[['Game Matchup', 'team', 'AP Top 25', 'season', 'season_type',
                                                            'week', 'start_date', 'conference_game']]

        condition_matchup_summary = (
                (df_matchup_home_away_all_data_sel_col['season'] == str(reporting_year)) &
                (df_matchup_home_away_all_data_sel_col['week'] == int(reporting_week)) &
                (df_matchup_home_away_all_data_sel_col['season_type'] == str(report_season_type))
        )

        df_matchup_summary = df_matchup_home_away_all_data_sel_col.loc[condition_matchup_summary]
        '''
        df_matchup_summary = df_matchup_home_away_all_data_sel_col.loc[
            df_matchup_home_away_all_data_sel_col['season'] == str(reporting_year)].loc[
            (df_matchup_home_away_all_data_sel_col['week'] == int(reporting_week)) & (df_cfb_for_reporting_game_matchup['season_type'] == str(report_season_type))]
        '''
        #Create DF for Matchup Summary Current Season Table
        df_matchup_home_away_all_data_current_season_sel_col = df_matchup_home_away_all_data_current_season[[
            'team', 'season', 'season_type', 'week', 'conference_game', 'home_vs_away', 'points', 'home_team', 'home_points',
            'home_line_scores', 'away_team', 'away_points', 'away_line_scores']]

        #Create DF additional Matchup Summary High Level Stats Info
        df_cfb_summary_home_away_append_sel_col = df_cfb_summary_home_away_append[['season', 'team', 'total.wins', 'total.losses',
                                                           'home_points_season_mean', 'away_points_season_mean',
                                                           'epa_per_game_offense_overall_avg_per_season',
                                                           'epa_per_game_offense_overall_avg_per_season']].reset_index()
        df_cfb_summary_matchup_reporting_year = df_cfb_summary_home_away_append_sel_col

        #Create figure for Matchup Summary Tables
        fig_df_matchup_summary = plt.figure("fig_matchup_summary", figsize=(10, 5))
        fig_df_matchup_summary.ax1 = fig_df_matchup_summary.add_subplot(311)
        fig_df_matchup_summary.ax1.axis('off')
        fig_df_matchup_summary.ax1.table(cellText=df_matchup_summary.values, colLabels=df_matchup_summary.columns)

        fig_df_matchup_summary.ax2 = fig_df_matchup_summary.add_subplot(312)
        fig_df_matchup_summary.ax2.axis('off')
        fig_df_matchup_summary.ax2.table(cellText=df_cfb_summary_matchup_reporting_year.values, colLabels=df_cfb_summary_matchup_reporting_year.columns)

        fig_df_matchup_summary.ax3 = fig_df_matchup_summary.add_subplot(313)
        fig_df_matchup_summary.ax3.axis('off')
        fig_df_matchup_summary.ax3.table(cellText=df_matchup_home_away_all_data_current_season_sel_col.values,
                  colLabels=df_matchup_home_away_all_data_current_season_sel_col.columns)

        #Create DF and figure for Season Stats Table
        df_matchup_season_stats_offense = df_cfb_season_stats_by_season_home_away_append[
            ['team', 'season', 'offense_possessionTime','offense_totalYards','offense_netPassingYards',
             'offense_passAttempts','offense_passCompletions','offense_passingTDs','offense_rushingYards',
             'offense_rushingAttempts','offense_rushingTDs','offense_turnovers','offense_fumblesLost','offense_passesIntercepted']]
        df_matchup_season_stats_offense_reporting_year = df_matchup_season_stats_offense.loc[
            df_matchup_season_stats_offense['season'] == str(reporting_year)]

        df_matchup_season_stats_offense_downs_and_turnovers = df_cfb_season_stats_by_season_home_away_append[
            ['team', 'season', 'offense_firstDowns','offense_thirdDowns','offense_thirdDownConversions',
             'offense_fourthDowns','offense_fourthDownConversions','offense_turnovers',
             'offense_fumblesLost','offense_passesIntercepted']]
        df_matchup_season_stats_offense_downs_and_turnovers_reporting_year = df_matchup_season_stats_offense_downs_and_turnovers.loc[
            df_matchup_season_stats_offense_downs_and_turnovers['season'] == str(reporting_year)]

        df_matchup_season_stats_defense = df_cfb_season_stats_by_season_home_away_append[
            ['team', 'season', 'defense_tacklesForLoss','defense_sacks','defense_fumblesRecovered',
             'defense_interceptions','defense_interceptionTDs']]
        df_matchup_season_stats_defense_reporting_year = df_matchup_season_stats_defense.loc[
            df_matchup_season_stats_defense['season'] == str(reporting_year)]

        df_matchup_season_stats_special_teams = df_cfb_season_stats_by_season_home_away_append[
            ['team', 'season', 'specialteams_kickReturns','specialteams_kickReturnYards','specialteams_kickReturnTDs',
             'specialteams_puntReturnYards','specialteams_puntReturns','specialteams_puntReturnTDs']]
        df_matchup_season_stats_special_teams_reporting_year = df_matchup_season_stats_special_teams.loc[
            df_matchup_season_stats_special_teams['season'] == str(reporting_year)]

        #Create Figure for Matchup Season Stats Offense
        fig_df_matchup_season_stats_offense = plt.figure("fig_matchup_season_stats", figsize=(10, 5))
        ax1 = fig_df_matchup_season_stats_offense.add_subplot(211)
        ax1 = plt.table(cellText=df_matchup_season_stats_offense.values,colLabels=df_matchup_season_stats_offense.columns)
        ax1 = plt.axis('off')

        ax2 = fig_df_matchup_season_stats_offense.add_subplot(212)
        ax2 = plt.table(cellText=df_matchup_season_stats_offense_downs_and_turnovers.values,colLabels=df_matchup_season_stats_offense_downs_and_turnovers.columns)
        ax2 = plt.axis('off')

        #Create Figure for Matchup Season Stats Defense and Special Teams
        fig_df_matchup_season_stats_defense_special_teams = plt.figure("fig_matchup_season_stats_defense_special_teams", figsize=(10, 5))
        ax1 = fig_df_matchup_season_stats_defense_special_teams.add_subplot(211)
        ax1 = plt.table(cellText=df_matchup_season_stats_defense.values,colLabels=df_matchup_season_stats_defense.columns)
        ax1 = plt.axis('off')

        ax2 = fig_df_matchup_season_stats_defense_special_teams.add_subplot(212)
        ax2 = plt.table(cellText=df_matchup_season_stats_special_teams.values,colLabels=df_matchup_season_stats_special_teams.columns)
        ax2 = plt.axis('off')

        #Create figures for report
        list_figures = []

        fig_matchup_team_points = sns.catplot(data=df_matchup_home_away_all_data, x="week", y="points",
                                              col="season", kind='bar', hue="team",
                                              height=4, aspect=1,
                                              palette={home_team:home_team_color, away_team:away_team_color})
        sns.set_style("whitegrid", {'grid.linestyle': '--'})
        list_figures.append(fig_matchup_team_points)

        fig_matchup_result_of_the_spread = sns.catplot(data=df_matchup_home_away_all_data, x="result_of_the_spread",
                                                       kind="count", col="season", hue="team",
                                                       height=4, aspect=1,
                                                       palette={home_team:home_team_color, away_team:away_team_color})
        sns.set_style("whitegrid", {'grid.linestyle': '--'})
        fig_matchup_result_of_the_spread.set_xticklabels(rotation=65, horizontalalignment='right')
        list_figures.append(fig_matchup_result_of_the_spread)

        fig_matchup_passing_success, axes = plt.subplots(1, 2)
        sns.set_style("whitegrid", {'grid.linestyle': '--'})
        sns.set(rc={"figure.figsize": (8, 4)})
        sns.lineplot(data=df_matchup_home_away_all_data_current_season, x="week", y="offense.passingPlays.successRate",
                     hue="team", palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[0],
                     marker="o")
        axes[0].set(xticks=df_matchup_home_away_all_data_current_season['week'])
        sns.lineplot(data=df_matchup_home_away_all_data_current_season, x="week", y="defense.passingPlays.successRate",
                     hue="team", palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[1], marker="o")
        axes[1].set(xticks=df_matchup_home_away_all_data_current_season['week'])
        fig_matchup_passing_success.tight_layout()
        list_figures.append(fig_matchup_passing_success)

        fig_matchup_rushing_success, axes = plt.subplots(1, 2)
        sns.set_style("whitegrid", {'grid.linestyle': '--'})
        sns.set(rc={"figure.figsize": (8, 4)})
        sns.lineplot(data=df_matchup_home_away_all_data_current_season, x="week", y="offense.rushingPlays.successRate",
                     hue="team", palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[0],
                     marker="o")
        axes[0].set(xticks=df_matchup_home_away_all_data_current_season['week'])
        sns.lineplot(data=df_matchup_home_away_all_data_current_season, x="week", y="defense.rushingPlays.successRate",
                     hue="team", palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[1],
                     marker="o")
        axes[1].set(xticks=df_matchup_home_away_all_data_current_season['week'])
        fig_matchup_rushing_success.tight_layout()
        list_figures.append(fig_matchup_rushing_success)

        fig_matchup_passing_rushing_yards, axes = plt.subplots(1, 2)
        sns.set_style("whitegrid", {'grid.linestyle': '--'})
        sns.set(rc={"figure.figsize": (8, 4)})
        sns.lineplot(data=df_matchup_home_away_all_data, x="season", y="offense_netPassingYards", hue="team",
                     palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[0], marker="o")
        sns.lineplot(data=df_matchup_home_away_all_data, x="season", y="offense_rushingYards", hue="team",
                     palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[1], marker="o")
        fig_matchup_passing_rushing_yards.tight_layout()
        list_figures.append(fig_matchup_passing_rushing_yards)

        fig_matchup_offense_defense_success, axes = plt.subplots(1, 2)
        sns.set_style("whitegrid", {'grid.linestyle': '--'})
        sns.set(rc={"figure.figsize": (8, 4)})
        sns.lineplot(data=df_matchup_home_away_all_data_current_season, x="week", y="offense.successRate",
                        hue="team", palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[0], marker="o")
        axes[0].set(xticks=df_matchup_home_away_all_data_current_season['week'])
        sns.lineplot(data=df_matchup_home_away_all_data_current_season, x="week", y="defense.successRate",
                        hue="team", palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[1], marker="o")
        axes[1].set(xticks=df_matchup_home_away_all_data_current_season['week'])
        fig_matchup_offense_defense_success.tight_layout()
        list_figures.append(fig_matchup_offense_defense_success)

        fig_matchup_offense_defense_zscores, axes = plt.subplots(1, 2)
        sns.set_style("whitegrid", {'grid.linestyle': '--'})
        sns.set(rc={"figure.figsize": (8, 4)})
        sns.lineplot(data=df_cfb_summary_home_away_append, x="season", y="offense_zscore_final", hue="team",
                      palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[0], marker="o")
        sns.lineplot(data=df_cfb_summary_home_away_append, x="season", y="defense_zscore_final", hue="team",
                      palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[1], marker="o")
        fig_matchup_offense_defense_zscores.tight_layout()
        list_figures.append(fig_matchup_offense_defense_zscores)

        fig_matchup_special_teams_total_zscores, axes = plt.subplots(1, 2)
        sns.set_style("whitegrid", {'grid.linestyle': '--'})
        sns.set(rc={"figure.figsize": (8, 4)})
        sns.lineplot(data=df_cfb_summary_home_away_append, x="season", y="specialteams_zscore_final", hue="team",
                      palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[0], marker="o")
        sns.lineplot(data=df_cfb_summary_home_away_append, x="season", y="total_zscore", hue="team",
                     palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[1], marker="o")
        fig_matchup_special_teams_total_zscores.tight_layout()
        list_figures.append(fig_matchup_special_teams_total_zscores)

        fig_matchup_epa_offense_defense, axes = plt.subplots(1, 2)
        sns.set_style("whitegrid", {'grid.linestyle': '--'})
        sns.set(rc={"figure.figsize": (10, 4)})
        sns.lineplot(data=df_matchup_home_away_all_data_current_season, x="week", y="offense.ppa",
                     hue="team", palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[0], marker="o")
        axes[0].set(xticks=df_matchup_home_away_all_data_current_season['week'])
        sns.lineplot(data=df_matchup_home_away_all_data_current_season, x="week", y="defense.ppa",
                     hue="team", palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[1], marker="o")
        axes[1].set(xticks=df_matchup_home_away_all_data_current_season['week'])
        fig_matchup_epa_offense_defense.tight_layout()
        list_figures.append(fig_matchup_epa_offense_defense)


        fig_matchup_epa_offense_defense_per_season, axes = plt.subplots(1, 2)
        sns.set_style("whitegrid", {'grid.linestyle': '--'})
        sns.set(rc={"figure.figsize": (10, 4)})
        sns.lineplot(data=df_matchup_home_away_all_data_current_season, x="week", y="epa_per_game_offense.overall",
                     hue="team", palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[0],
                     marker="o")
        sns.lineplot(data=df_matchup_home_away_all_data_current_season, x="week", y="epa_per_game_defense.overall",
                     hue="team", palette={home_team: home_team_color, away_team: away_team_color}, ax=axes[1],
                     marker="o")
        fig_matchup_epa_offense_defense_per_season.tight_layout()
        list_figures.append(fig_matchup_epa_offense_defense_per_season)

        '''
        fig_matchup_all_teams_zscore = sns.displot(data=cfb_all_data_reporting_year, x ="offense_zscore_final", hue="team",
                                                   palette={home_team: home_team_color, away_team: away_team_color, 'team': 'black'})

        sns.set(rc={"figure.figsize": (8, 4)})
        list_figures.append(fig_matchup_all_teams_zscore)
        '''

        #Output DF's and Figures to Report
        filename_team_report = file_path_cfb_reports_reporting_year_week + str(matchup) + ".pdf"
        pp = PdfPages(filename_team_report)
        pp.savefig(fig_df_matchup_summary, bbox_inches='tight')
        for fig in list_figures:
            fig.savefig(pp, format='pdf')
        pp.savefig(fig_df_matchup_season_stats_offense, bbox_inches='tight')
        pp.savefig(fig_df_matchup_season_stats_defense_special_teams, bbox_inches='tight')
        pp.close()
        plt.close('all')
        print('Report Generated for ' + str(matchup))


def pdf_matchup_reports_new(reporting_year, reporting_week, report_season_type):
    print('Generating Reports for current week of the year')
    reporting_year = str(reporting_year)
    file_path_cfb_reports = cwd + '/reports/cfb/'
    file_path_cfb_reports_reporting_year = file_path_cfb_reports + str(reporting_year) + '/'
    file_path_cfb_reports_reporting_year_week_season_type = file_path_cfb_reports_reporting_year + str(report_season_type) + '/'
    file_path_cfb_reports_reporting_year_week = file_path_cfb_reports_reporting_year_week_season_type + 'Week_' + str(reporting_week) + '/'

    cfb_season_week_matchups = load.sqlite_query_table('cfb_reporting_season_week_matchups')
    cfb_matchup_all_data = load.sqlite_query_table('cfb_reporting_matchup_all_data')
    cfb_team_info = load.sqlite_query_table('cfb_reporting_team_info')
    cfb_summary = load.sqlite_query_table('cfb_reporting_summary')
    cfb_season_stats_by_season = load.sqlite_query_table('cfb_reporting_season_stats_by_season')

    df_cfb_for_reporting_game_matchup = cfb_season_week_matchups[cfb_season_week_matchups['season'].astype(str).str.contains(reporting_year)]
    df_cfb_for_reporting_game_matchup_reporting_week = df_cfb_for_reporting_game_matchup.loc[(df_cfb_for_reporting_game_matchup['week'] == int(reporting_week)) & (df_cfb_for_reporting_game_matchup['season_type'] == str(report_season_type))]
    cfb_matchup_all_data_reporting_year = cfb_matchup_all_data.loc[cfb_matchup_all_data['season'] == str(reporting_year)]

    for index, row in df_cfb_for_reporting_game_matchup_reporting_week.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        matchup = row['Game Matchup']
        df_home_team_all_data = cfb_matchup_all_data.loc[cfb_matchup_all_data['team'] == home_team]
        df_away_team_all_data = cfb_matchup_all_data.loc[cfb_matchup_all_data['team'] == away_team]
        home_team_color = cfb_team_info.loc[cfb_team_info['team'] == home_team, 'color'].iloc[0]
        away_team_color = cfb_team_info.loc[cfb_team_info['team'] == away_team, 'color'].iloc[0]
        team_colors = {
            home_team: home_team_color,  # blue
            away_team: away_team_color  # orange
        }
        df_matchup_home_away_all_data = pd.concat([df_home_team_all_data, df_away_team_all_data], ignore_index=True)
        df_matchup_home_away_all_data_current_season = df_matchup_home_away_all_data.loc[
            df_matchup_home_away_all_data['season'] == str(reporting_year)]

        df_cfb_summary_home_team = cfb_summary.loc[cfb_summary['team'] == (home_team)]
        df_cfb_summary_away_team = cfb_summary.loc[cfb_summary['team'] == (away_team)]
        df_cfb_summary_home_away_append = pd.concat([df_cfb_summary_home_team, df_cfb_summary_away_team], ignore_index=True).reset_index()

        df_cfb_season_stats_by_season_home_team = cfb_season_stats_by_season.loc[cfb_season_stats_by_season['team'] == (home_team)]
        df_cfb_season_stats_by_season_away_team = cfb_season_stats_by_season.loc[cfb_season_stats_by_season['team'] == (away_team)]
        df_cfb_season_stats_by_season_home_away_append = pd.concat([df_cfb_season_stats_by_season_home_team, df_cfb_season_stats_by_season_away_team], ignore_index=True)
        df_cfb_season_stats_by_season_home_away_append.sort_values(by=['season','team'], inplace=True, ascending=False)

        matchup_data = df_matchup_home_away_all_data.loc[df_matchup_home_away_all_data['Game Matchup'] == str(matchup)]


        def pdf_page_1(matchup_data, cfb_summary, home_team, away_team):
            matchup_data_columns = matchup_data[
                ['Game Matchup', 'team', 'AP Top 25', 'season', 'season_type', 'week', 'start_date', 'conference_game']]
            season_summary_columns = ['season', 'team', 'total.wins', 'total.losses', 'home_points_season_mean',
                                      'away_points_season_mean', 'epa_per_game_offense_overall_avg_per_season',
                                      'epa_per_game_offense_overall_avg_per_season']
            cfb_summary_filtered = cfb_summary.loc[
                (cfb_summary['team'] == home_team) | (cfb_summary['team'] == away_team)]
            cfb_summary_filtered_values = [cfb_summary_filtered[col] for col in season_summary_columns]

            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=False,
                vertical_spacing=0.03,
                specs=[[{"type": "table"}],
                       [{"type": "table"}]]
            )
            fig.add_trace(go.Table(
                header=dict(
                    values=[col for col in matchup_data_columns.columns],
                    font=dict(size=10),
                    align="left"
                ),
                cells=dict(
                    values=[matchup_data[col].tolist() for col in matchup_data_columns.columns],
                    align="left"
                )
            ), row=1, col=1)
            fig.add_trace(go.Table(
                header=dict(
                    values=season_summary_columns,
                    font=dict(size=10),
                    align="left"
                ),
                cells=dict(
                    values=cfb_summary_filtered_values,
                    align="left"
                )
            ), row=2, col=1)
            fig.update_layout(
                height=800,
                width=1200,
                showlegend=False,
                title_text="Matchup Summary"
            )
            #fig.show()
            return fig

        def pdf_page_2(reporting_year, df_matchup_home_away_all_data, subplot_title, team_colors):
            df_matchup_home_away_all_data['spread_counts'] = 1
            seasons = list(range(int(reporting_year), int(reporting_year) - 5, -1))
            subplot_col_number = len(seasons)

            figures_points = []
            figures_spread = []

            for season in seasons:
                df = df_matchup_home_away_all_data.loc[df_matchup_home_away_all_data['season'] == str(season)]
                df['spread_counts'] = 1
                fig = px.bar(
                    df,
                    x="week",
                    y="points",
                    barmode="group",
                    color='team',
                    color_discrete_map=team_colors
                )
                fig.update_xaxes(type='category')  # Ensure x-axis shows all values
                figures_points.append(fig)

            for season in seasons:
                df = df_matchup_home_away_all_data.loc[df_matchup_home_away_all_data['season'] == str(season)]
                fig = px.bar(
                    df,
                    x="result_of_the_spread",
                    y="spread_counts",
                    barmode="group",
                    color='team',
                    color_discrete_map=team_colors
                )
                fig.update_xaxes(type='category')
                figures_spread.append(fig)

            fig = make_subplots(
                rows=2,
                cols=subplot_col_number,
                subplot_titles=[str(season) for season in seasons] * 2,
                shared_yaxes=True
            )

            # Track which teams have been added to the legend
            added_teams = set()

            for i, figure in enumerate(figures_points):
                for trace in figure.data:
                    if trace.name in added_teams:
                        trace.showlegend = False
                    else:
                        trace.showlegend = True
                        added_teams.add(trace.name)
                    fig.add_trace(trace, row=1, col=i + 1)

            for i, figure in enumerate(figures_spread):
                for trace in figure.data:
                    if trace.name in added_teams:
                        trace.showlegend = False
                    else:
                        trace.showlegend = True
                        added_teams.add(trace.name)
                    fig.add_trace(trace, row=2, col=i + 1)

            fig.update_layout(
                height=1200,
                width=1200,
                title_text=subplot_title,
                showlegend=True,
                xaxis=dict(tickmode='linear'),
                #yaxis=dict(tickmode='linear'),
                margin=dict(t=100, b=100, l=50, r=50)  # Adjust margins to prevent clipping

            )

            for col in range(1, subplot_col_number + 1):
                fig.update_xaxes(
                    tickmode='linear',
                    tickangle=45,
                    row=1,
                    col=col
                )
                fig.update_yaxes(
                    showticklabels=True,
                    showgrid=True,
                    row=1,
                    col=col
                )
                fig.update_xaxes(
                    tickmode='linear',
                    tickangle=45,
                    row=2,
                    col=col
                )
                fig.update_yaxes(
                    showticklabels=True,
                    showgrid=True,
                    row=2,
                    col=col
                )
            '''
            # Ensure the x-axis and y-axis shows for all subplots
            for i in range(1, subplot_col_number + 1):
                fig.update_xaxes(type='linear', row=1, col=i)
                fig.update_xaxes(type='linear', row=2, col=i)
                fig.update_yaxes(showticklabels=True, showgrid=True, row=1, col=i)
                fig.update_yaxes(showticklabels=True, showgrid=True, row=2, col=i)
            '''
            #fig.show()
            return(fig)

        def pdf_page_3(reporting_year, df_matchup_home_away_all_data, subplot_title, team_colors):
            fig_offense_passing_success_report_year_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'offense.passingPlays.successRate', home_team, away_team,
                reporting_year, team_colors)

            fig_defense_passing_success_report_year_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'defense.passingPlays.successRate', home_team, away_team,
                reporting_year, team_colors)

            fig_offense_rushing_success_report_year_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'offense.rushingPlays.successRate', home_team, away_team,
                reporting_year, team_colors)

            fig_defense_rushing_success_report_year_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'defense.rushingPlays.successRate', home_team, away_team,
                reporting_year, team_colors)

            fig_offense_successRate_report_year_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'offense.successRate', home_team, away_team, reporting_year,
                team_colors)
            fig_defense_successRate_report_year_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'defense.successRate', home_team, away_team, reporting_year,
                team_colors)

            subplot_rows = 3
            subplot_cols = 2
            fig = make_subplots(
                rows=subplot_rows,
                cols=subplot_cols,
                subplot_titles=[
                    'Offense Passing Success Rate',
                    'Defense Passing Success Rate',
                    'Offense Rushing Success Rate',
                    'Defense Rushing Success Rate',
                    'Offense Success Rate',
                    'Defense Success Rate'
                ],
                shared_yaxes=False
            )

            # Track which teams have been added to the legend
            added_teams = set()

            for trace in fig_offense_passing_success_report_year_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=1, col=1)

            for trace in fig_defense_passing_success_report_year_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=1, col=2)

            for trace in fig_offense_rushing_success_report_year_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=2, col=1)

            for trace in fig_defense_rushing_success_report_year_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=2, col=2)

            for trace in fig_offense_successRate_report_year_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=3, col=1)

            for trace in fig_defense_successRate_report_year_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=3, col=2)

            # Update layout
            fig.update_layout(
                height=1200,
                width=1200,
                title_text=subplot_title,
                showlegend=True
            )
            for row in range(1, subplot_rows + 1):
                for col in range(1, subplot_cols + 1):
                    fig.update_xaxes(
                        tickmode='linear',
                        tickangle=45,
                        row=row,
                        col=col
                    )
                    fig.update_yaxes(
                        showticklabels=True,
                        showgrid=True,
                        row=row,
                        col=col
                    )
            #fig.show()
            return fig

        def pdf_page_4(reporting_year, df_matchup_home_away_all_data, subplot_title, team_colors):

            fig_offense_netPassingYards_report_year_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'offense_netPassingYards', home_team, away_team, reporting_year,
                team_colors)
            fig_offense_rushingYards_report_year_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'offense_rushingYards', home_team, away_team, reporting_year,
                team_colors)
            fig_epa_offense_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'offense.ppa', home_team, away_team, reporting_year, team_colors)
            fig_epa_defense_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'defense.ppa', home_team, away_team, reporting_year, team_colors)
            fig_epa_per_game_offense_by_season_box = plays.matchup_stats_by_report_year_box(
                df_matchup_home_away_all_data, 'season', 'epa_per_game_offense.overall', home_team, away_team,
                team_colors)
            fig_epa_per_game_defense_by_season_box = plays.matchup_stats_by_report_year_box(
                df_matchup_home_away_all_data, 'season', 'epa_per_game_defense.overall', home_team, away_team,
                team_colors)

            subplot_rows = 3
            subplot_cols = 2

            fig = make_subplots(
                rows=subplot_rows,
                cols=subplot_cols,
                subplot_titles=[
                    'Offense Net Passing Yards',
                    'Offense Rushing Yards',
                    'Offensive EPA',
                    'Defense EPA',
                    'Offense EPA Per Game by Season',
                    'Defense EPA Per Game by Season'
                ],
                shared_yaxes=False,
            )
            # Track which teams have been added to the legend
            added_teams = set()

            for trace in fig_offense_netPassingYards_report_year_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=1, col=1)

            for trace in fig_offense_rushingYards_report_year_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=1, col=2)

            for trace in fig_epa_offense_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=2, col=1)

            for trace in fig_epa_defense_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=2, col=2)

            for trace in fig_epa_per_game_offense_by_season_box.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=3, col=1)

            for trace in fig_epa_per_game_defense_by_season_box.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=3, col=2)

            fig.update_layout(
                height=1200,
                width=1200,
                title_text=subplot_title,
                showlegend=True,
                xaxis=dict(tickmode='linear'),
            )

            for row in range(1, subplot_rows + 1):
                for col in range(1, subplot_cols + 1):
                    fig.update_xaxes(
                        tickmode='linear',
                        tickangle=45,
                        row=row,
                        col=col
                    )
                    fig.update_yaxes(
                        showticklabels=True,
                        showgrid=True,
                        row=row,
                        col=col
                    )
            #fig.show()
            return fig
        def pdf_page_5(reporting_year, df_matchup_home_away_all_data, subplot_title, team_colors):

            fig_offense_zscore_final_report_year_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'offense_zscore_final', home_team, away_team, reporting_year,
                team_colors)
            fig_defense_zscore_final_report_year_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'defense_zscore_final', home_team, away_team, reporting_year,
                team_colors)
            fig_specialteams_zscore_final_report_year_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'specialteams_zscore_final', home_team, away_team,
                reporting_year, team_colors)
            fig_total_zscore_report_year_line = plays.matchup_stats_by_report_year_line(
                df_matchup_home_away_all_data, 'week', 'total_zscore', home_team, away_team, reporting_year,
                team_colors)

            subplot_rows = 2
            subplot_cols = 2

            fig = make_subplots(
                rows=subplot_rows,
                cols=subplot_cols,
                subplot_titles=[
                    'Offense Zscore',
                    'Defense Zscore',
                    'Special Teams Zscore',
                    'Total Zscore',
                ],
                shared_yaxes=False,
            )

            # Track which teams have been added to the legend
            added_teams = set()

            for trace in fig_offense_zscore_final_report_year_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=1, col=1)

            for trace in fig_defense_zscore_final_report_year_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=1, col=2)

            for trace in fig_specialteams_zscore_final_report_year_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=2, col=1)

            for trace in fig_total_zscore_report_year_line.data:
                if trace.name in added_teams:
                    trace.showlegend = False
                else:
                    trace.showlegend = True
                    added_teams.add(trace.name)
                fig.add_trace(trace, row=2, col=2)

            fig.update_layout(
                height=1200,
                width=1200,
                title_text=subplot_title,
                showlegend=True
            )

            for row in range(1, subplot_rows + 1):
                for col in range(1, subplot_cols + 1):
                    fig.update_xaxes(
                        tickmode='linear',
                        tickangle=45,
                        row=row,
                        col=col
                    )
                    fig.update_yaxes(
                        showticklabels=True,
                        showgrid=True,
                        row=row,
                        col=col
                    )

            #fig.show()
            return fig

        def pdf_page_6(cfb_season_stats_by_season, home_team, away_team, subplot_title):
            fig_matchup_stats_offense_table = plays.matchup_stats_table(cfb_season_stats_by_season, home_team,
                                                                        away_team, 'offense')
            fig_matchup_stats_offense_downs_table = plays.matchup_stats_table(cfb_season_stats_by_season, home_team,
                                                                              away_team, 'offense_downs')
            fig_matchup_stats_defense_table = plays.matchup_stats_table(cfb_season_stats_by_season, home_team,
                                                                        away_team, 'defense')
            fig_matchup_stats_special_teams_table = plays.matchup_stats_table(cfb_season_stats_by_season, home_team,
                                                                              away_team, 'special_teams')

            fig = make_subplots(
                rows=4,
                cols=1,
                subplot_titles=[
                    'Offense Stats',
                    'Offense Downs Stats',
                    'Defense Stats',
                    'Special Teams Stats',
                ],
                specs=[[{"type": "table"}],
                       [{"type": "table"}],
                       [{"type": "table"}],
                       [{"type": "table"}]]
            )
            for trace in fig_matchup_stats_offense_table.data:
                fig.add_trace(trace, row=1, col=1)
            for trace in fig_matchup_stats_offense_downs_table.data:
                fig.add_trace(trace, row=2, col=1)
            for trace in fig_matchup_stats_defense_table.data:
                fig.add_trace(trace, row=3, col=1)
            for trace in fig_matchup_stats_special_teams_table.data:
                fig.add_trace(trace, row=4, col=1)

            fig.update_layout(
                height=1200,  # Adjust height as needed
                width=1200,  # Adjust width as needed
                title_text=subplot_title,
            )
            #fig.show()
            return fig

        fig_pdf_page_1 = pdf_page_1(matchup_data, cfb_summary, home_team, away_team)
        fig_pdf_page_2 = pdf_page_2(reporting_year, df_matchup_home_away_all_data, "Points by Season", team_colors)
        fig_pdf_page_3 = pdf_page_3(reporting_year, df_matchup_home_away_all_data,"Success Rate by Report Year", team_colors)
        fig_pdf_page_4 = pdf_page_4(reporting_year, df_matchup_home_away_all_data,"Passing/Rushing Rates and EPA", team_colors)
        fig_pdf_page_5 = pdf_page_5(reporting_year, df_matchup_home_away_all_data,"Zscores", team_colors)
        fig_pdf_page_6 = pdf_page_6(matchup_data, home_team, away_team, "Stats Tables")

        figures = [
            fig_pdf_page_1,
            fig_pdf_page_2,
            fig_pdf_page_3,
            fig_pdf_page_4,
            fig_pdf_page_5,
            fig_pdf_page_6
        ]

        filename_team_report = file_path_cfb_reports_reporting_year_week + str(matchup) + ".pdf"
        pdf_pages = matplotlib.backends.backend_pdf.PdfPages(filename_team_report)

        def plotly_to_image(fig):
            # Convert Plotly figure to image with specified resolution
            return pio.to_image(fig, format='png', width=fig.layout.width, height=fig.layout.height)

        dpi = 300  # Set DPI for high resolution
        for fig in figures:
            # Convert Plotly figure to image
            img_data = plotly_to_image(fig)
            img_stream = io.BytesIO(img_data)
            img = plt.imread(img_stream, format='png')

            # Adjust figure size to fit the image
            fig_width, fig_height = img.shape[1] / dpi, img.shape[0] / dpi
            # Increase dimensions by a factor (e.g., 1.5 to make the image larger in the PDF)
            plt.figure(figsize=(fig_width * 1.9, fig_height * 1.9), dpi=dpi)

            # Plot the image
            plt.imshow(img)
            plt.axis('off')
            pdf_pages.savefig()  # Save the figure to the PDF
            plt.close()

        pdf_pages.close()
        print('Report Generated for ' + str(matchup))
