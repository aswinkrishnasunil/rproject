import time
from dbConnection import SqlDbConn
from time import gmtime, strftime
from datetime import date, timedelta
import pandas as pd
# import dropbox_token_refresh as dbtr
import os
#import dropbox
import warnings
warnings.filterwarnings('ignore')

falcon_notifications = 'https://hooks.slack.com/services/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'
class PostShinyShipMap:
    """
    This class encapsulates various functions for retrieving, processing, and posting data related to LNG ships.

    It includes functions for gathering ship data, tracking data, historical progression data, and posting data
    to Dropbox. Each function serves a specific purpose in managing and analyzing LNG ship information.

    Please refer to the individual function comments for detailed descriptions of their functionality.
    """
    def __init__(self):
        try:
            self.db_obj = SqlDbConn()
            self.eff_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())  # Create variable for today's time
            self.projectFolder = os.getcwd()
        except Exception as e:
            print('Variable declaration error: {}'.format(str(e)))

    def port_data(self):
        """
        Retrieve LNG port data from the database.

        This function queries the database for LNG port data where the type is 'port'
        and returns the data as a Pandas DataFrame.

        Returns:
            pd.DataFrame: A DataFrame containing LNG port data.
        """
        try:
            port_data = pd.read_sql_query('''select * from [dbo].[LNG_port] where type = 'port' ''', self.db_obj.dbConn())
            return port_data
        except Exception as e:
            print('Port data function error: {}'.format(str(e)))

    def idle_master_days_data(self):
        """
        Retrieve data for the maximum idle days of LNG ships in the last 7 days.

        This function queries the database for maximum idle days of LNG ships
        for the 'Max24-5' model in the last 7 days, and returns the data as a Pandas DataFrame.

        Returns:
            pd.DataFrame: A DataFrame containing data for maximum idle days.
        """
        try:
            idle_master_days = pd.read_sql_query('''select imo, date_ as date, idle from LNG_idle_ship_days_max_eff 
            where model = 'Max24-5' order by imo, date_ desc''', self.db_obj.dbConn())
            previous_date = date.today() - timedelta(7)
            idle_7day = idle_master_days[idle_master_days['date'] >= previous_date]
            return idle_7day
        except Exception as e:
            print('Idle Master days data function error: {}'.format(str(e)))

    def data(self):  # Tracking data
        """
        Retrieve tracking data for LNG ships.

        This function queries the database for tracking data of LNG ships, including
        ship information, location, destination, and more. It returns the data as a Pandas DataFrame.

        Returns:
            pd.DataFrame: A DataFrame containing tracking data for LNG ships.
        """
        try:
            data = pd.read_sql_query("""
            WITH l AS (
                SELECT DISTINCT(sub_region2) AS sub_region, 
                        region2 AS region 
                FROM LNG_port 
                WHERE sub_region IS NOT NULL
            ), r AS (
                SELECT imo, region AS dest, dest AS sub_region, prob, d2d, eta,source_region, source_subregion, source_port, pr_port, pr_port_id, port_prob, port_d2d, port_eta, effective_dt 
                FROM LNG_l1A_results 
                LEFT JOIN l ON dest = sub_region 
                WHERE effective_dt = (
                        SELECT MAX(effective_dt) 
                        FROM LNG_l1A_results 
                    ) 
                    AND d2d IS NOT NULL
            ),
            max_seen_dates AS (
                SELECT imo, MAX(seen_date) AS max_seen_date
                FROM sdr.dbo.LNG_tracking where lat is not null AND lon is not null AND heading is not null AND draft is not null 
                GROUP BY imo
            )
            SELECT DISTINCT t.imo, seen_date, lat, lon, heading, t.dest AS stated_destination, t.eta AS stated_eta, 
                    scrape, sog, name, dwt, gas_cap, ((gas_cap / 2.21) * 0.0000487) AS bcf_cap, 
                    CASE 
                        WHEN gas_cap <= 145000 THEN 'Conventional' 
                        WHEN gas_cap > 145000 AND gas_cap <= 220000 THEN 'Q-Flex' 
                        WHEN gas_cap > 220000 THEN 'Q-Max' 
                    END AS size, draft, empty_draft, r.dest AS model_dest,source_region,source_subregion, source_port, prob, sub_region, d2d, 
                    r.eta AS model_eta, pr_port, pr_port_id, port_prob, port_d2d, port_eta
            FROM sdr.dbo.LNG_tracking t 
            LEFT JOIN sdr.dbo.LNG_ships s ON s.imo = t.imo 
            INNER JOIN r ON r.imo = t.imo 
            JOIN max_seen_dates m ON t.imo = m.imo AND t.seen_date >= DATEADD(dd, -3, m.max_seen_date)
            WHERE s.active = 1 
                AND [Tanker/FPSO] = 'Tanker'
                AND lat is not null AND lon is not null AND heading is not null AND draft is not null 
            ORDER BY t.imo, seen_date;

            """, self.db_obj.dbConn())
            return data
        except Exception as e:
            print('Data function error: {}'.format(str(e)))

    def yy_ship_count(self):  # yy ship count
        """
        Retrieve YY ship count data and save it to a CSV file.

        This function queries the database to calculate YY ship count data based on various criteria,
        including ship drafts, idleness, and destinations. The resulting data is saved to a CSV file.

        The YY ship count data includes columns: 'imo', 'empty_full', 'idle', 'subregion', and 'region'.

        The CSV file is saved in the 'output' folder of the project folder.

        Returns:
            None
        """
        try:
            print('Gathering yy_ship_count data..')
            yy_ship_count = pd.read_sql_query("""     
            with ef as(
            select o.imo, date, ef
            from lng_ocean_regions_max_eff o
            inner join lng_ships s on s.imo = o.imo
            where active = 1 and [Tanker/FPSO] = 'Tanker' and date = CONVERT(DATE, DATEADD(DAY, -365, GETDATE()))
            ), idle as(
            select o.imo, date_ as date, idle
            from LNG_idle_ship_days_max_eff o
            inner join lng_ships s on s.imo = o.imo
            where active = 1 and [Tanker/FPSO] = 'Tanker' and model = 'Max24-5' and date_ = CONVERT(DATE, DATEADD(DAY, -365, GETDATE()))
            ), yy as (	select ef.imo, ef.date, ef.ef, idle.idle from ef
            full join idle on ef.imo = idle.imo and ef.date = idle.date)
            select yy.imo, yy.ef empty_full, yy.idle, sr.begin_region, sr.end_region region, sr.begin_subregion,
            sr.end_subregion subregion, sr.begin_port_name, sr.end_port_name port_name from yy
            inner join LNG_voyage_sr2 sr
            on sr.imo = yy.imo and yy.date <= sr.end_date and yy.date >= sr.begin_date
            """, self.db_obj.dbConn())
            yy_ship_count = yy_ship_count[["imo", "empty_full", "idle", "begin_subregion","subregion", "begin_region","region","begin_port_name", "port_name"]]
            yy_ship_count.to_csv(self.projectFolder + "/output/yy_ship_count.csv", index=False)
            # print('Gathering yy_ship_count data Completed!')
        except Exception as e:
            print('YY ship count data function error: {}'.format(str(e)))

    def tracking_data(self):
        """
        Retrieve and save tracking data to a CSV file.

        This function gathers tracking data, which includes information such as ship location,
        destination, and related details. The data is retrieved and saved to a CSV file.

        The CSV file is saved in the 'output' folder of the project folder.

        Returns:
            None
        """
        try:
            print('Gathering Tracking data ..')
            tracking = self.data()
            tracking = tracking[
                ["imo", "seen_date", "lat", "lon", "heading", "stated_destination", "stated_eta", "scrape", "sog",
                 "draft"]]

            tracking.to_csv(self.projectFolder + "/output/tracking_data2.csv", index=False)
            # print('Gathering Tracking data Completed!')
        except Exception as e:
            print('Tracking data function error: {}'.format(str(e)))

    def imo_data(self):
        """
        Retrieve and save IMO data to a CSV file.

        This function gathers IMO data, which includes various ship details, origins, idleness,
        and maximum draft information. The data is retrieved, processed, and saved to a CSV file.

        The CSV file is saved in the 'output' folder of the project folder.

        Returns:
            None
        """
        try:
            print('Gathering IMO data..')
            data = self.data()
            imo = data[
                ["imo", "name", "dwt", "gas_cap", "bcf_cap", "size", "empty_draft", "model_dest", "prob", "sub_region","source_subregion","source_region", "source_port",
                 "d2d", "model_eta","pr_port", "pr_port_id", "port_prob", "port_d2d", "port_eta"]].drop_duplicates().reset_index(drop=True)
            origin = pd.read_sql_query('''select o.imo, origin_name, origin_type from LNG_origin o inner join LNG_ships
                               s on s.imo= o.imo where active=1 and [Tanker/FPSO] = 'Tanker' ''', self.db_obj.dbConn())
            origin = origin[["imo", "origin_name", "origin_type"]]
            imo = pd.merge(imo, origin, on="imo", how="left")
            idle_7day = self.idle_master_days_data()
            idle_7day = idle_7day.sort_values(['imo', 'date'], axis=0, ascending=True)
            idle_7day['idle_days'] = 0
            if idle_7day['idle'].values[0] == 1:
                idle_7day['idle_days'].values[0] = 1
            idle_7day = idle_7day.reset_index()
            idle_7day.drop('index', axis=1, inplace=True)
            for i in range(1, idle_7day.shape[0]):
                if idle_7day['imo'].iloc[i - 1] == idle_7day['imo'].iloc[i]:
                    if idle_7day['idle'].values[i] == 1:
                        idle_7day.idle_days.iloc[i] = idle_7day.idle_days.iloc[i - 1] + 1
                else:
                    if idle_7day['idle'].values[i] == 1:
                        idle_7day.idle_days.iloc[i] = 1
            for i in range(0, idle_7day.shape[0]):
                if (idle_7day.idle_days.iloc[i]) != 0:
                    idle_7day.idle.iloc[i] = idle_7day.idle_days.iloc[i]
            df = pd.DataFrame(idle_7day, columns=['imo', 'date'])
            idle_df = df.groupby('imo')['date'].agg(max).reset_index()
            idle_df = pd.merge(idle_7day[['imo', 'date', 'idle']], idle_df, on=['imo', 'date'], how='right')
            imo = pd.merge(imo, idle_df, on=['imo'], how='left')
            imo['idle'] = imo['idle'].fillna(0)
            # query_insert = """
            # DECLARE @StartDate DATE = DATEADD(YEAR, -6, CONVERT(DATE, GETDATE()));
            # DECLARE @CallingApplication VARCHAR(400) = 'Unassigned';
            # DECLARE @Refresh CHAR(1) = 'N';
            # IF OBJECT_ID('tempdb..#temp_results') IS NOT NULL
            #     DROP TABLE #temp_results;
            # CREATE TABLE #temp_results (
            #     begin_date       DATE,
            #     end_date         DATE,
            #     voyage_id        INT,
            #     imo              INT,
            #     begin_region     VARCHAR(100),
            #     end_region       VARCHAR(100),
            #     begin_subregion  VARCHAR(100),
            #     end_subregion    VARCHAR(100),
            #     dwt              FLOAT,
            #     draft            FLOAT,
            #     cargo            VARCHAR(5),
            #     gas_cap          FLOAT,
            #     gas_volume       FLOAT,
            #     begin_port_id    INT,
            #     begin_port_name  VARCHAR(200),
            #     end_port_id      INT,
            #     end_port_name    VARCHAR(200)
            # );
            # INSERT INTO #temp_results (begin_date, end_date, voyage_id, imo, begin_region, end_region, begin_subregion, end_subregion, dwt, draft, cargo, gas_cap, gas_volume, begin_port_id, begin_port_name, end_port_id, end_port_name)
            # EXECUTE [SDR].[dbo].[sp_Report_LNG_ship_dep_sr2] @CallingApplication, @Refresh, @StartDate;
            #  """
            # cursor =  self.db_obj.dbConn().cursor()
            # cursor.execute(query_insert)
            query_fetch = """SELECT sd.imo, MAX(sd.draft) AS max_draft
            FROM lng_ship_dep_sr2 sd
            INNER JOIN lng_ships s ON s.imo = sd.imo
            WHERE sd.cargo = 'Full' AND s.active = 1 AND s.[Tanker/FPSO] = 'Tanker'
            GROUP BY sd.imo; """
            max_draft_table = pd.read_sql(query_fetch,  self.db_obj.dbConn())
            # cursor.close()
            imo = pd.merge(imo, max_draft_table, on=['imo'], how='left')
            imo['max_draft'] = imo['max_draft'].fillna(12)
            imo.loc[imo["max_draft"] > 14, "max_draft"] = 14
            # imo.to_csv("imo_data2.csv", index=False)
            # max_draft_table = pd.read_sql_query('''select sd.imo, max(draft) as max_draft from lng_ship_dep_sr2 sd
            # inner join lng_ships s on s.imo = sd.imo where begin_date >= dateadd(yy,-6,convert(date, getdate()))
            # and cargo = 'Full' and active = 1 and [Tanker/FPSO] = 'Tanker' group by sd.imo''', self.db_obj.dbConn())
            # imo = pd.merge(imo, max_draft_table, on=['imo'], how='left')
            # imo['max_draft'] = imo['max_draft'].fillna(12)
            # imo.loc[imo["max_draft"] > 14, "max_draft"] = 14
            imo.to_csv(self.projectFolder + "/output/imo_data2.csv", index=False)

            # notification to slack

            # print('Gathering IMO data Completed!')
        except Exception as e:
            print('imo data function error: {}'.format(str(e)))

    def flow_historical_forecasts(self):
        """
        Retrieve and save historical progression data for LNG forecasts.

        This function gathers historical progression data for LNG forecasts, including information
        such as ship regions, subregions, gas volumes, and dates. The data is retrieved and saved to a CSV file.

        The CSV file is saved in the 'output' folder of the project folder.

        Returns:
            None
        """
        try:
            df1 = pd.DataFrame()
            print('Gathering Historical Progression data ..')
            for i in range(1, 8):
                j = -i
                temp = pd.read_sql_query(f'''select imo, region, subregion, region2, subregion2, 
                date, type, gas_volume 
                from lng_forecast_progression 
                where max_eff = (select max(max_eff) from lng_forecast_progression 
                where convert(date,max_eff) <= dateadd(d, {j}, convert(date,getdate())))''', self.db_obj.dbConn())
                temp['t'] = i
                df1 = pd.concat([df1,temp], ignore_index=True)
                # df1 = df1.append(temp, ignore_index=True)
            df1.to_csv(self.projectFolder + "/output/LNG_Region_Flow_Historical_Forecasts.csv", index=False)
            # print('Gathering Historical Progression data Completed!')
        except Exception as e:
            print('flow_historical_forecasts function error: {}'.format(str(e)))

    def post_data(self):
        try:
            # Dropbox access token
            ACCESS_TOKEN = dbtr.refresh_token()
            # Initialize Dropbox client
            dbx = dropbox.Dropbox(ACCESS_TOKEN)
            query_fetch_ef = """SELECT o.imo, ef
            FROM lng_ocean_regions_max_eff o
            INNER JOIN lng_ships s ON s.imo = o.imo
            WHERE active = 1 AND [Tanker/FPSO] = 'Tanker' AND date = (select max(date) from lng_ocean_regions_max_eff)"""
            ef_data = pd.read_sql(query_fetch_ef,  self.db_obj.dbConn())
            imo = pd.read_csv('output/imo_data2.csv')
            tracking = pd.read_csv('output/tracking_data2.csv')
            yy_ship_count_data = pd.read_csv('output/yy_ship_count.csv')

            imo_tracking = tracking.merge(imo, how='left', on='imo')
            imo_tracking = imo_tracking.merge(ef_data, how='left', on='imo')
            imo_tracking["port_prob"] = imo_tracking["port_prob"].round(4)
            imo_tracking = imo_tracking[["date", "lat", "lon", "imo", "seen_date",
                                         "name", "draft", "empty_draft", "sog", "stated_destination",
                                         "model_dest", "prob","source_region","source_subregion","source_port", "stated_eta", "d2d", "model_eta", "pr_port", "pr_port_id", "port_prob", "port_d2d", "port_eta", "size", "bcf_cap",
                                         "origin_name", "origin_type", "sub_region", "idle", "gas_cap", "dwt",
                                         "max_draft", "ef"]]
            imo_tracking = imo_tracking.dropna(subset=["lat", "lon", "imo", "seen_date"])
            imo_tracking['seen_date'] = pd.to_datetime(imo_tracking['seen_date'], format='%Y-%m-%d %H:%M:%S')
            # imo_tracking['port_eta'] = pd.to_datetime(imo_tracking['port_eta'], format='%Y-%m-%d %H:%M')
            imo_tracking.drop_duplicates(subset=['lat','lon','seen_date','imo'],inplace=True)
            imo_tracking.to_csv('output/imo_tracking.csv', index=False)

            # yy_imo_data = imo_tracking.groupby('imo').head(1).reset_index(drop=True)
            # yy_ship_count_data = pd.merge(yy_ship_count_data, yy_imo_data[["imo","source_region","source_subregion","origin_name"]], on='imo', how='inner')
            # yy_ship_count_data.to_csv(self.projectFolder + "/output/yy_ship_count.csv", index=False)
            # posting data to dropbox
            # with open('output/imo_tracking.csv', "rb") as file:
            #     dbx.files_upload(file.read(), '/imo_tracking.csv', mode=dropbox.files.WriteMode.overwrite)
            #
            # with open('output/yy_ship_count.csv', "rb") as file:
            #     dbx.files_upload(file.read(), '/yy_ship_count.csv', mode=dropbox.files.WriteMode.overwrite)
            #
            # with open('output/LNG_Region_Flow_Historical_Forecasts.csv', "rb") as file:
            #     # print( dbx.files_upload(file.read(), '/LNG_Region_Flow_Historical_Forecasts.csv', mode=dropbox.files.WriteMode.overwrite))
            #     # time.sleep(5)
            #     dbx.files_upload(file.read(), '/LNG_Region_Flow_Historical_Forecasts.csv', mode=dropbox.files.WriteMode.overwrite)
            # print('done')

        except Exception as e:
            print('Error while posting data to the DropBox: {}'.format(str(e)))


if __name__ == "__main__":
    print('Running..')
    main = PostShinyShipMap()
    main.port_data()
    main.data()
    main.yy_ship_count()
    main.tracking_data()
    main.imo_data()
    main.flow_historical_forecasts()
    main.post_data()

# data = pd.read_sql_query("""
# WITH l AS (
#     SELECT DISTINCT(sub_region2) AS sub_region,
#            region2 AS region
#     FROM LNG_port
#     WHERE sub_region IS NOT NULL
# ), r AS (
#     SELECT imo, region AS dest, dest AS sub_region, prob, d2d, eta,source_region, source_subregion, source_port, pr_port, pr_port_id, port_prob, port_d2d, port_eta, effective_dt
#     FROM LNG_l1A_results
#     LEFT JOIN l ON dest = sub_region
#     WHERE model_name = 'S6 NN v4'
#       AND effective_dt = (
#           SELECT MAX(effective_dt)
#           FROM LNG_l1A_results
#           WHERE model_name = 'S6 NN v4'
#       )
#       AND d2d IS NOT NULL
# )
# SELECT t.imo, seen_date, lat, lon, heading, t.dest AS stated_destination, t.eta AS stated_eta,
#        scrape, sog, name, dwt, gas_cap, ((gas_cap / 2.21) * 0.0000487) AS bcf_cap,
#        CASE
#            WHEN gas_cap <= 145000 THEN 'Conventional'
#            WHEN gas_cap > 145000 AND gas_cap <= 220000 THEN 'Q-Flex'
#            WHEN gas_cap > 220000 THEN 'Q-Max'
#        END AS size, draft, empty_draft, r.dest AS model_dest,source_region,source_subregion, source_port, prob, sub_region, d2d,
#        r.eta AS model_eta, pr_port, pr_port_id, port_prob, port_d2d, port_eta
# FROM sdr.dbo.LNG_tracking t
# LEFT JOIN sdr.dbo.LNG_ships s ON s.imo = t.imo
# LEFT JOIN r ON r.imo = t.imo
# WHERE seen_date >= DATEADD(dd, -3, CONVERT(date, GETDATE()))
#   AND s.active = 1
#   AND [Tanker/FPSO] = 'Tanker'
#   AND lat is not null AND lon is not null AND heading is not null AND draft is not null
# ORDER BY t.imo, seen_date;
# """, self.db_obj.dbConn())