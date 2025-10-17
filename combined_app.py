import streamlit as st
import pandas as pd
import io
import sys


# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(layout="wide", page_title="Kabaddi QC Tool")

# st.title("Kabaddi Data Processing & QC Tool - Old Dashboard")
st.markdown(
    '<h1>Kabaddi Data Processing & QC tool - <span style="color:yellow;">New Dashboard</span></h1>',
    unsafe_allow_html=True)

###################
match_id = st.text_input("Enter Match ID", value = "6464")
match_id = int(match_id)
###################

st.markdown("")

# --- Upload CSV ---
uploaded_file = st.file_uploader("Upload raw Kabaddi CSV, process it, and download the cleaned output.", type=["csv"])

if uploaded_file:
    # Store raw_df in session_state for safe access
    st.session_state.raw_df = pd.read_csv(
        uploaded_file, delimiter=';', header=None, dtype=str, skiprows=1
    )

    # --- Show Total Rows and Columns ---
    rows, cols = st.session_state.raw_df.shape if st.session_state.raw_df is not None else (0, 0)
    st.write(f"**RAW File: Total rows:** `{rows}` | **Total columns:** `{cols}`")

    # --- Show first 5 rows of raw file ---
    st.subheader("Raw File Preview")
    st.dataframe(st.session_state.raw_df, height=210)

    # CSS to style the Process button
    st.markdown(
    """
    <style>
    div.stButton>button {
        color: yellow !important;
        font-weight: bolder !important;
        font-size: 30px !important;  /* Increase font size */
        background-color: black !important;
        border: none !important;
        padding: 10px 20px !important; /* Makes button bigger */
    }
    </style>
    """,
    unsafe_allow_html=True)

    # --- Process Button ---
    if st.button("Process CSV", use_container_width=True):

        st.subheader("Quality Check Logs")
        log_output = io.StringIO()
        sys.stdout = log_output  # Capture all print statements

        try:
            # Save uploaded file temporarily in Streamlit environment
            temp_file_path = "temp_raw.csv"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            raw_file_name = temp_file_path
            output_file_name = "processed_output.csv"


            # Define raw_df before using it
            raw_df = st.session_state.raw_df.copy()

            # Step 2: Find the row where the first column is strictly "Name"
            header_row_idx_search = raw_df[raw_df.iloc[:, 0].astype(str).str.strip() == "Name"].index

            if header_row_idx_search.empty:
                print("❌ Could not find a row strictly equal to 'Name'.")
                sys.exit()

            header_row_idx = header_row_idx_search[0]

            # Step 3: Use that row as the header, and keep only the rows below it
            df = raw_df.copy()
            df.columns = df.iloc[header_row_idx].astype(str).str.strip()
            df = df.iloc[header_row_idx + 1:].reset_index(drop=True)

            # Step 4: Keep only rows where first column strictly starts with "Raid "
            df = df[df.iloc[:, 0].astype(str).str.strip().str.startswith("Raid ")].reset_index(drop=True)

            if df.empty:
                print("❌ No rows found strictly starting with 'Raid '.")
                sys.exit()

             # Step 5: Rename Columns
            new_col_names = [
                'Name','Time','Start','Stop','Team','Player','Raid 1','Raid 2','Raid 3',
                'D1','D2','D3','D4','D5','D6','D7','Successful','Empty','Unsuccessful',
                'Bonus','No Bonus','Z1','Z2','Z3','Z4','Z5','Z6','Z7','Z8','Z9','RT0',
                'RT1','RT2','RT3','RT4','RT5','RT6','RT7','RT8','RT9','DT0','DT1','DT2',
                'DT3','DT4','Hand touch','Running hand touch','Toe touch','Running Kick',
                'Reverse Kick','Side Kick','Defender self out','Body hold',
                'Ankle hold','Single Thigh hold','Push','Dive','DS0','DS1','DS2','DS3','In Turn',
                'Out Turn','Create Gap','Jump','Dubki','Struggle','Release','Block','Chain_def','Follow',
                'Technical Point','All Out', *(f'RL{i}' for i in range(1, 31)),
                'Raider self out','Running Bonus','Centre Bonus','LCorner','LIN','LCover','Center',
                'RCover','RIN','RCorner','Flying Touch','Double Thigh Hold','Flying Reach','Clean','Not Clean',
                # Extra 4 columns
                'Yes','No','Z10','Z11']

            if len(df.columns) == len(new_col_names):
                df.columns = new_col_names
            else:
                print(f"❌ Column mismatch: got {len(df.columns)}, expected {len(new_col_names)}")
                sys.exit()

            # =========================================================================
            # START: Part 2 - Transformation and QCs
            # This part now uses the 'df' from above instead of reading a new file.
            # =========================================================================
            
            ini_match = 6464

            # ------ Define IDs ------
            tour_id = "T001"
            seas_id = "S12"
            match_no = match_id - ini_match + 1
            match_id = "M"+str(match_id)

            # ---------------- Drop unused columns ----------------
            df.drop(['Time', 'Team'], axis=1, inplace=True, errors='ignore')


            # -------- Raid_Number --------
    
            for c in ['Raid 1', 'Raid 2', 'Raid 3']:
                df[c] = pd.to_numeric(df[c].astype(str).str.strip().replace('', '0'), errors='coerce').fillna(0).astype(int)

            df.loc[df['Raid 2'] == 1, 'Raid 2'] = 2
            df.loc[df['Raid 3'] == 1, 'Raid 3'] = 3

            df['Raid_Number'] = df['Raid 1'] + df['Raid 2'] + df['Raid 3']
            df.drop(['Raid 1', 'Raid 2', 'Raid 3'], axis=1, inplace=True)


            # ------ Rename key columns ------
        
            df.rename(columns={
                'Name': 'Event_Number',
                'Technical Point': 'Technical_Point',
                'All Out': 'All_Out'
            }, inplace=True)

        
            # ------ Number_of_Defenders ------

            defender_cols = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7']
            for idx, col in enumerate(defender_cols, 1):
                df[col] = pd.to_numeric(df[col].astype(str).str.strip().replace('', '0'),
                                        errors='coerce').fillna(0).astype(int)
                df[col] = df[col].apply(lambda x: idx if x == 1 else 0)
            df['Number_of_Defenders'] = df[defender_cols].sum(axis=1).astype(int)
            df.drop(columns=defender_cols, inplace=True)

            # ------ Outcome ------

            # 1. Ensure numeric conversion
            for col in ['Successful', 'Empty', 'Unsuccessful']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # 2. Map 1 → label, 0 → empty string
            df['Successful'] = df['Successful'].map({1: 'Successful', 0: ''})
            df['Empty'] = df['Empty'].map({1: 'Empty', 0: ''})
            df['Unsuccessful'] = df['Unsuccessful'].map({1: 'Unsuccessful', 0: ''})

            # 3. Safely join non-empty labels
            df['Outcome'] = df[['Successful', 'Empty', 'Unsuccessful']].apply(
                lambda row: ' '.join(val for val in row if val != ''), axis=1)

            df.drop(['Successful', 'Empty', 'Unsuccessful'], axis=1, inplace=True)

            # ------ Bonus ------

            df_bonus = df[['Bonus', 'No Bonus', 'Centre Bonus', 'Running Bonus']].copy()

            # Convert to integers to avoid string concatenation issues
            for col in df_bonus.columns:
                df_bonus[col] = pd.to_numeric(df_bonus[col], errors='coerce').fillna(0).astype(int)

            # Create unified "Bonus" indicator
            df_bonus['Bonus'] = df_bonus[['Bonus', 'Centre Bonus', 'Running Bonus']].max(axis=1)
            df_bonus['Bonus'] = df_bonus['Bonus'].map({1: 'Yes', 0: ''})

            df_bonus['No Bonus'] = df_bonus['No Bonus'].map({1: 'No', 0: ''})

            # Combine cleanly
            df_bonus['Bonus'] = (df_bonus['Bonus'] + ' ' + df_bonus['No Bonus']).str.strip()

            # If all are 0 → set Bonus to "No"
            df_bonus.loc[(df_bonus[['Bonus', 'No Bonus']] == '').all(axis=1),'Bonus'] = 'No'

            df_bonus.drop(columns=['No Bonus', 'Centre Bonus', 'Running Bonus'], inplace=True)

            # ------ Type_of_Bonus ------

            bonus_cols = ['Bonus', 'Centre Bonus', 'Running Bonus']

            # Ensure numeric 0/1
            for col in bonus_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # Map 1 → column name, 0 → blank
            for col in bonus_cols:
                df[col] = df[col].map({1: col, 0: ''})

            # Join them safely
            df['Type_of_Bonus'] = df[bonus_cols].apply(
                lambda x: ' '.join(v for v in x if v != ''), axis=1)

            # Drop original raw bonus columns
            df.drop(columns=bonus_cols + ['No Bonus'], inplace=True, errors='ignore')

            # Merge final clean Bonus column back into main df
            df = pd.concat([df_bonus, df], axis=1)

            # ------ Zone_of_Action ------

            zone_cols = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6', 'Z7', 'Z8', 'Z9', 'Z10', 'Z11']

            # Convert to integers first (handles '0', '1', blanks)
            for col in zone_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # Replace 1 → column name, 0 → blank
            for col in zone_cols:
                df[col] = df[col].map({1: col, 0: ''})

            # Join zone names cleanly
            df['Zone_of_Action'] = df[zone_cols].apply(
                lambda x: ' '.join(v for v in x if v != ''), axis=1)

            df.drop(columns=zone_cols, inplace=True)

            # ------ Raiding_Team_Points ------

            rt_cols = ['RT0', 'RT1', 'RT2', 'RT3', 'RT4', 'RT5', 'RT6', 'RT7', 'RT8', 'RT9']

            # Convert to integers first
            for col in rt_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # Replace 1 → its numeric suffix (e.g., RT3 → 3)
            for col in rt_cols:
                num = int(col.replace("RT", ""))
                df[col] = df[col].map({1: num, 0: 0})

            # Sum up points
            df['Raiding_Team_Points'] = df[rt_cols].sum(axis=1).astype(int)
            df.drop(columns=rt_cols, inplace=True)


            # ----------- Defending_Team_Points -----------

            dt_cols = ['DT0', 'DT1', 'DT2', 'DT3', 'DT4']
            for col in dt_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                num = int(col.replace("DT", ""))
                df[col] = df[col].map({1: num, 0: 0})

            df['Defending_Team_Points'] = df[dt_cols].sum(axis=1).astype(int)
            df.drop(columns=dt_cols, inplace=True)


            # ------ Attacking_Skill ----------

            att_skill_cols = ['Hand touch', 'Running hand touch', 'Toe touch', 'Running Kick', 'Reverse Kick',
                                'Side Kick', 'Defender self out', 'Flying Touch']

            # 1. Clean and convert to integers (0/1)
            for col in att_skill_cols:
                df[col] = df[col].astype(str).str.strip()  # Remove extra spaces
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # 2. Map 1 → skill name, 0 → blank
            for col in att_skill_cols:
                df[col] = df[col].map({1: col, 0: ''})

            # 3. Join all non-empty skills into a single string
            df['Attacking_Skill'] = df[att_skill_cols].apply(
            lambda x: ', '.join([v for v in x if v != '']).strip(), axis=1)

            df.drop(columns=att_skill_cols, inplace=True)

            
            # ------------- Defensive_Skill --------------

            ds_skill_cols = ['Body hold', 'Ankle hold', 'Single Thigh hold', 'Double Thigh Hold', 'Push', 'Dive', 'Block',
                                'Chain_def', 'Follow', 'Raider self out']

            # 1. Clean and convert to integers (0/1)
            for col in ds_skill_cols:
                df[col] = df[col].astype(str).str.strip()  # Remove extra spaces
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # 2. Map 1 → skill name, 0 → blank
            for col in ds_skill_cols:
                df[col] = df[col].map({1: col, 0: ''})

            # 3. Join all non-empty skills into a single string
            df['Defensive_Skill'] = df[ds_skill_cols].apply(
                lambda x: ', '.join([v for v in x if v != '']).strip(), axis=1)

            df.drop(columns=ds_skill_cols, inplace=True)

            # ------------ Number_of_Defenders_Self_Out --------------

            dso_cols = ['DS0', 'DS1', 'DS2', 'DS3']
            for col in dso_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                num = int(col.replace("DS", ""))
                df[col] = df[col].map({1: num, 0: 0})

            df['Number_of_Defenders_Self_Out'] = df[dso_cols].sum(axis=1).astype(int)
            df.drop(columns=dso_cols, inplace=True)

            
            # ------ Counter_Action_Skill ------

            ca_cols = ['In Turn', 'Out Turn', 'Create Gap', 'Jump', 'Dubki', 'Struggle', 'Release', 'Flying Reach']

            # 1. Clean and convert to integers (0/1)
            for col in ca_cols:
                df[col] = df[col].astype(str).str.strip()  # Remove extra spaces
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # 2. Map 1 → skill name, 0 → blank
            for col in ca_cols:
                df[col] = df[col].map({1: col, 0: ''})

            # 3. Join all non-empty skills into a single string
            df['Counter_Action_Skill'] = df[ca_cols].apply(
                lambda x: ', '.join([v for v in x if v != '']).strip(), axis=1)
            df.drop(columns=ca_cols, inplace=True)


            # ------ Defender_Positions ------

            def_pos_cols = ['LCorner', 'LIN', 'LCover', 'Center', 'RCover', 'RIN', 'RCorner']

            # 1. Clean and convert to integers (0/1)
            for col in def_pos_cols:
                df[col] = df[col].astype(str).str.strip()  # Remove extra spaces
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # 2. Map 1 → skill name, 0 → blank
            for col in def_pos_cols:
                df[col] = df[col].map({1: col, 0: ''})

            # 3. Join all non-empty skills into a single string
            df['Defender_Position'] = df[def_pos_cols].apply(
                lambda x: ', '.join([v for v in x if v != '']).strip(), axis=1)
            df.drop(columns=def_pos_cols, inplace=True)

            
            # ------ QoD_Skill ------

            qod_cols = ['Clean', 'Not Clean']
            # 1. Clean and convert to integers (0/1)
            for col in qod_cols:
                df[col] = df[col].astype(str).str.strip()  # Remove extra spaces
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # 2. Map 1 → skill name, 0 → blank
            for col in qod_cols:
                df[col] = df[col].map({1: col, 0: ''})

            # 3. Join all non-empty skills into a single string
            df['QoD_Skill'] = df[qod_cols].apply(
                lambda x: ', '.join([v for v in x if v != '']).strip(), axis=1)

            df.drop(columns=qod_cols, inplace=True)

            # ---------------- Raiding Length ----------------

            rl_cols = [f'RL{i}' for i in range(1, 31)]

            for col in rl_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                num = int(col.replace("RL", ""))
                df[col] = df[col].map({1: num, 0: 0})

            # Calculate Actual Raid_Length
            df['Raid_Length'] = 30 - df[rl_cols].sum(axis=1).astype(int)
            df.drop(columns=rl_cols, inplace=True)

            # ---------------- Match Metadata ----------------

            n = len(df)
            df['Tournament_ID'] = tour_id
            df['Season_ID'] = seas_id
            df['Match_No'] = match_no
            df['Match_ID'] = match_id
            df['Match_Raid_Number'] = range(1, n + 1)

            
            # ---------------- Raider & Defenders Names ----------------

            # Split by "|" (tolerate spaces), expand to separate columns
            parts = df['Player'].str.split(r'\s*\|\s*', expand=True)

            # Keep only the names after the dash, strip spaces, and make Title case
            names = parts.apply(lambda s: s.str.split('-', n=1).str[1].str.strip().str.title())

            # Ensure we have Raider + up to 7 Defenders (add empty cols if needed)
            needed_cols = 1 + 7  # 1 raider + 7 defenders
            if names.shape[1] < needed_cols:
                for _ in range(needed_cols - names.shape[1]):
                    names[names.shape[1]] = None
            # or if there are extra columns, drop them
            names = names.iloc[:, :needed_cols]

            # Rename columns
            names = names.rename(columns={
                0: 'Raider_Name',
                1: 'Defender_1_Name',
                2: 'Defender_2_Name',
                3: 'Defender_3_Name',
                4: 'Defender_4_Name',
                5: 'Defender_5_Name',
                6: 'Defender_6_Name',
                7: 'Defender_7_Name'
            })

            # Drop original and join the new columns
            df = df.drop(columns='Player').join(names)

            
            # ---------------- Start & End Time ----------------

            # Remove milliseconds
            df['Start'] = df['Start'].str.split(',').str[0]
            df['Stop'] = df['Stop'].str.split(',').str[0]

            # --- Helper to handle both mm:ss and hh:mm:ss ---
            def parse_time(t):
                parts = list(map(int, t.split(":")))
                if len(parts) == 2:   # mm:ss
                    m, s = parts
                    return pd.Timedelta(minutes=m, seconds=s)
                elif len(parts) == 3: # hh:mm:ss
                    h, m, s = parts
                    return pd.Timedelta(hours=h, minutes=m, seconds=s)

            # Convert to timedeltas
            df['start_td'] = df['Start'].apply(parse_time)
            df['stop_td'] = df['Stop'].apply(parse_time)

            # Duration
            df['duration'] = df['stop_td'] - df['start_td']

            # Total seconds
            df['total_secs'] = df['duration'].dt.total_seconds()

            # Format as mm:ss (ignores hours, rolls into minutes)
            df['Time'] = df['total_secs'].apply(lambda x: f"{int(x//60):02}:{int(x%60):02}")

            # Clean up
            df.drop(columns=['start_td', 'stop_td', 'duration', 'total_secs', 'Stop', 'Start'], inplace=True)


            # ---------------- Tie Break Raids ----------------

            tie_cols = ['Yes', 'No']
            for col in tie_cols:
                df[col] = df[col].astype(str).str.strip()  # Remove extra spaces
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # 2. Map 1 → skill name, 0 → blank
            for col in tie_cols:
                df[col] = df[col].map({1: col, 0: ''})

            # 3. Join all non-empty skills into a single string
            df['Tie_Break_Raids'] = df[tie_cols].apply(
                lambda x: ', '.join([v for v in x if v != '']).strip(), axis=1)

            df.drop(columns=tie_cols, inplace=True)

            
            # ---------------- New Columns ----------------
            new_columns = [
                # --- Extra Columns ---
                'Video_Link', 'Video', 'Event', 'YC_Extra', 'Team_ID',                # 5

                # --- TEAM RAID NUMBERING ---
                'Team_Raid_Number', 'Defender_1', 'Defender_2',
                'Defender_3', 'Defender_4', 'Defender_5',
                'Defender_6', 'Defender_7',                                            # 8

                # --- TEAMS & PLAYERS IDENTIFICATION ---
                'Raiding_Team_ID', 'Raiding_Team_Name',
                'Defending_Team_ID', 'Defending_Team_Name',
                'Player_ID', 'Raider_ID',                                              # 6

                # --- POINTS BREAKDOWN ---
                'Raiding_Team_Points_Pre', 'Defending_Team_Points_Pre',
                'Raiding_Touch_Points', 'Raiding_Bonus_Points',
                'Raiding_Self_Out_Points', 'Raiding_All_Out_Points',
                'Defending_Capture_Points', 'Defending_Bonus_Points',
                'Defending_Self_Out_Points', 'Defending_All_Out_Points',               # 10

                # --- RAID ACTION DETAILS ---
                'Court_Entry', 'Number_of_Raiders', 'Raider_Self_Out',
                'Defenders_Touched_or_Caught', 'Half'                                   # 5
            ]

            # Add empty new columns
            for col in new_columns:
                df[col] = None

            
            # ---------------- New Logical Order ----------------
            new_order = [

                # 1. Raid Details & Identification
                "Season_ID", "Tournament_ID", "Match_No",
                "Match_ID", "Event_Number", "Match_Raid_Number",
                "Team_Raid_Number", "Raid_Number",
                "Half", "Time", "Raid_Length",                                                               # 11

                # 2. Raid Outcome & Scoring
                "Outcome", "All_Out", "Bonus", "Type_of_Bonus", "Technical_Point", "Raider_Self_Out",
                "Raiding_Touch_Points", "Raiding_Bonus_Points",
                "Raiding_Self_Out_Points", "Raiding_All_Out_Points", "Raiding_Team_Points",
                "Defending_Capture_Points", "Defending_Bonus_Points",
                "Defending_Self_Out_Points", "Defending_All_Out_Points", "Defending_Team_Points",
                "Number_of_Raiders", "Defenders_Touched_or_Caught",
                "Raiding_Team_Points_Pre", "Defending_Team_Points_Pre", "Zone_of_Action",                     # 21

                # 3. Player & Team Info
                "Raider_Name", "Court_Entry", "Player_ID",
                "Raider_ID", "Raiding_Team_ID",
                "Raiding_Team_Name", "Defending_Team_ID",
                "Defending_Team_Name",                                                                          # 8

                # 4. Defenders’ Info
                "Number_of_Defenders", "Defender_Position",
                "Defender_1", "Defender_1_Name", "Defender_2", "Defender_2_Name",
                "Defender_3", "Defender_3_Name", "Defender_4", "Defender_4_Name",
                "Defender_5", "Defender_5_Name", "Defender_6", "Defender_6_Name",                              # 17
                "Defender_7", "Defender_7_Name",
                "Number_of_Defenders_Self_Out",                                                               
            
                # 5. Skills & Actions
                "Attacking_Skill", "Defensive_Skill", "QoD_Skill",
                "Counter_Action_Skill", "Tie_Break_Raids",                                                     # 5

                # 6. Video & Event Metadata
                "Video_Link", "Video", "Event", "YC_Extra", "Team_ID"                                           # 5
            ]

            df = df[new_order]
            
            # ---------------- Updating Points Columns ----------------

            # Raiding_Bonus_Points
            df["Raiding_Bonus_Points"] = (df["Bonus"] == "Yes").astype(int)

            # Raiding_Touch_Points
            defender_cols = ['Defender_1_Name', 'Defender_2_Name', 'Defender_3_Name',
                            'Defender_4_Name', 'Defender_5_Name', 'Defender_6_Name', 'Defender_7_Name']
            df['Raiding_Touch_Points'] = 0
            mask = df['Outcome'] == 'Successful'
            df.loc[mask, 'Raiding_Touch_Points'] = (
                df.loc[mask, defender_cols].notna().sum(axis=1)
                - df.loc[mask, 'Number_of_Defenders_Self_Out']
                )
            
            # Convert 'All_Out' column to numeric directly
            df['All_Out'] = pd.to_numeric(df['All_Out'], errors='coerce')
            
            # Update Raiding_All_Out_Points
            df["Raiding_All_Out_Points"] = (((df['Outcome'] == 'Successful') & (df["All_Out"] == 1)).astype(int) * 2)
            
            # Raiding_Self_Out_Points
            df['Raiding_Self_Out_Points'] = df['Number_of_Defenders_Self_Out']

            # Defending_Bonus_Points
            df['Defending_Bonus_Points'] = (((df['Number_of_Defenders'] <= 3) & (df['Outcome'] == 'Unsuccessful')).astype(int))

            # Raider_Self_Out (helper col for defense logic)
            df["Raider_Self_Out"] = (df["Defensive_Skill"] == "Raider self out").astype(int)

            # Defending_Capture_Points
            df['Defending_Capture_Points'] = (((df['Outcome'] == 'Unsuccessful') & (df['Raider_Self_Out'] == 0)).astype(int))

            # Defending_All_Out_Points
            df["Defending_All_Out_Points"] = (((df['Outcome'] == 'Unsuccessful') & (df["All_Out"] == 1)).astype(int) * 2)

            # Defending_Self_Out_Points
            df['Defending_Self_Out_Points'] = df["Raider_Self_Out"]

            # Copy Outcome to Event
            df['Event'] = df['Outcome']

            # Video Column
            df['Video'] = range(1, len(df) +1)


            ######## Quality Check #########

            # QC 1: Empty Columns (Robust Version)

            cols_qc1 = [
                'Raid_Length', 'Outcome', 'Bonus', 'All_Out', 
                'Raid_Number', 'Raider_Name', 'Number_of_Defenders', 'Tie_Break_Raids'
            ]

            # Define a function to check for empty-like values
            def is_empty(val):
                if pd.isna(val):               # NaN values
                    return True
                val_str = str(val).strip()     # Convert to string and strip whitespace
                if val_str == '' or val_str.lower() in ['na', 'nan']:  # Empty or placeholders
                    return True
                return False

            # Apply function to all columns of interest
            mask = df[cols_qc1].applymap(is_empty)

            # Find rows with any empty column
            invalid_rows = df[mask.any(axis=1)]

            if not invalid_rows.empty:
                for idx, row in invalid_rows.iterrows():
                    empty_cols = mask.loc[idx][mask.loc[idx]].index.tolist()
                    print(f"\n❌ {row['Event_Number']}: Empty in columns → {', '.join(empty_cols)}. Please check and update.\n")
            else:
                print("\nQC 1: ✅ All rows are completely filled.\n")


            
            # QC 2: Whem Outcome = Empty These Columns must be Empty.

            # Ensure the columns we are checking numerically are actually numbers.
            # This is the key fix for the incorrect error messages.
            numeric_cols = ['All_Out', 'Raiding_Team_Points', 'Defending_Team_Points']
            for col in numeric_cols:
                # Convert column to a number, forcing errors into NaN, then fill NaN with 0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)


            cols_qc2 = ['Defender_1_Name', 'Defender_2_Name', 'Defender_3_Name', 'Defender_4_Name', 'Defender_5_Name', 'Defender_6_Name',
                        'Defender_7_Name', 'Attacking_Skill', 'Defensive_Skill', 'Counter_Action_Skill', 'Zone_of_Action','Defender_Position', 'QoD_Skill']
            
            cols_empty_qc2 = df[cols_qc2].replace('', pd.NA).isna().all(axis=1)

            # This mask will now work correctly because the data types are correct
            mask_qc2_invalid = (
                (df['Outcome'] == 'Empty') & ~(
                    cols_empty_qc2 &
                    (df['All_Out'] == 0) &
                    (df['Raiding_Team_Points'] == 0) &
                    (df['Defending_Team_Points'] == 0) &
                    (df['Bonus'] == 'No')
                )
            )

            if mask_qc2_invalid.any():
                for idx, row in df[mask_qc2_invalid].iterrows():
                    issues = []
                    
                    non_empty_cols = row[cols_qc2].replace('', pd.NA).dropna().index.tolist()
                    if non_empty_cols:
                        issues.append(f"these columns should be empty: {', '.join(non_empty_cols)}")

                    if row['All_Out'] != 0:
                        issues.append(f"All_Out should be 0 (is {row['All_Out']})")
                    if row['Raiding_Team_Points'] != 0:
                        issues.append(f"Raiding_Team_Points should be 0 (is {row['Raiding_Team_Points']})")
                    if row['Defending_Team_Points'] != 0:
                        issues.append(f"Defending_Team_Points should be 0 (is {row['Defending_Team_Points']})")
                    if row['Bonus'] != 'No':
                        issues.append(f"Bonus should be 'No' (is '{row['Bonus']}')")
                    
                    issue_string = '; '.join(issues)
                    print(f"❌ {row['Event_Number']}: → When Outcome is 'Empty', → {issue_string}.\n")
            else:
                print("QC 2: ✅ All rows meet conditions for Outcome = 'Empty'.\n")


            # QC 3: Successful / Unsuccessful with Bonus = No & Raider_Self_Out = 0

            cols_qc3 = ['Defender_1_Name', 'Number_of_Defenders', 'Zone_of_Action']
            non_empty_outcomes = (
                df['Outcome'].isin(['Successful', 'Unsuccessful'])
            ) & (df['Bonus'] == 'No') & (df['Raider_Self_Out'] == 0)
            cols_filled_qc3 = df[cols_qc3].replace('', pd.NA).notna().all(axis=1)
            mask_qc3_invalid = non_empty_outcomes & ~cols_filled_qc3
            if mask_qc3_invalid.any():
                for idx, row in df[mask_qc3_invalid].iterrows():
                    empty_cols = row[cols_qc3].replace('', pd.NA).isna()
                    missing_cols = empty_cols[empty_cols].index.tolist()
                    print(f"❌ {row['Event_Number']}: When Outcome='{row['Outcome']}', Bonus='No', Raider_Self_Out = 'No' → Missing: {', '.join(missing_cols)}.\n")
            else:
                print("QC 3: ✅ All rows are Valid.\n")


            # QC 4: If Raid_Number = 3 then row at index -2 must have Outcome == 'Empty'
            error_found = False
            
            for idx, row in df.iterrows():
                if row['Raid_Number'] == 3:
                    target_idx = idx - 2
                    # Only check if index - 2 exists
                    if target_idx >= 0:
                        if df.loc[target_idx, 'Outcome'] != 'Empty':
                            print(
                                f"❌ {df.loc[target_idx, 'Event_Number']}: → Outcome must be 'Empty' "
                                f"(Because {row['Event_Number']} has Raid_Number = 3)\n"
                            )
                            error_found = True
                    # If target_idx < 0, just skip silently
            
            # Final message
            if not error_found:
                print("QC 4: ✅ All rows are Valid.\n")

                    # If target_idx < 0, just skip silently

    
            # QC 5: If Raid_Number = 1 & Outcome = 'Empty', then row at index +2 must have Raid_Number = 2
            error_found = False

            for idx, row in df.iterrows():
                if (row['Raid_Number'] == 1) and (row['Outcome'] == 'Empty'):
                    target_idx = idx + 2
                    if target_idx < len(df) and df.loc[target_idx, 'Raid_Number'] != 2:
                        print(
                            f"❌ {df.loc[target_idx, 'Event_Number']}: → Raid_Number must be = 2 "
                            f"(Because {row['Event_Number']} Raid_Number is 1)\n"
                        )
                        error_found = True

            # Final message
            if not error_found:
                print("QC 5: ✅ All rows are Valid.\n")


            # QC 6: If Outcome = 'Successful or Unsuccessful', then row at index +2 must have Raid_Number = 1

            # Reset index to make position-based indexing safe
            df2 = df.reset_index(drop=True)

            error_found = False

            for i in range(len(df2)):
                outcome = str(df2.loc[i, 'Outcome']).strip().lower()

                # Rule: If Outcome is 'Successful' or 'Unsuccessful'
                if outcome in ('successful', 'unsuccessful'):
                    current_event = df2.loc[i, 'Event_Number'] 
                    target = i + 2

                    # If we are at the end of the DataFrame (no row +2), just skip
                    if target >= len(df2):
                        continue  # no error because there is no row +2 to check

                    # Get info for the target row
                    target_event = df2.loc[target, 'Event_Number']
                    target_raid_number = df2.loc[target, 'Raid_Number']

                    # If Raid_Number is not 1, this is a violation
                    if target_raid_number != 1:
                        print(
                            f"❌ {target_event}: → Raid_Number must be = 1 "
                            f"(Because {current_event} has Outcome = {df2.loc[i, 'Outcome']})\n"
                        )
                        error_found = True

            # Final message if no errors were found
            if not error_found:
                print("QC 6: ✅ All rows are Valid.\n")


            # QC 7: if Raid_Number = 2 & Outcome = 'Empty', then row at index -2 must have Raid_Number = 1 & Outcome = 'Empty'
            
            errors_found = False

            for idx, row in df.iterrows():
                if row['Raid_Number'] == 2 and row['Outcome'] == 'Empty':
                    if idx >= 2:
                        prev_row = df.loc[idx - 2]

                        # Check if either condition fails
                        if prev_row['Raid_Number'] != 1 or prev_row['Outcome'] != 'Empty':
                            # Printing with a comment style output
                            print(
                                f"❌ {row['Event_Number']} is Empty, but {prev_row['Event_Number']} has {prev_row['Raid_Number']} Raid Number and Outcome='{prev_row['Outcome']}'\n")
                            errors_found = True

            if not errors_found:
                print("QC 7: ✅ All rows are correct.\n")


            # QC 8: Attacking & Defensive Points match

            def check_points(cols, total_col, label):
                # print(f"\nChecking {label} → '{total_col}'")
                mismatch = df[cols].sum(axis=1) != df[total_col]
                if mismatch.any():
                    for idx, row in df[mismatch].iterrows():
                        print(f"❌ {row['Event_Number']}: → {label} mismatch (Expected: {df.loc[idx, cols].sum()}, Found: {row[total_col]})\n")
                else:
                    print(f"QC 8: ✅ All rows are correct for {label}\n")

            check_points(
                ['Raiding_Touch_Points','Raiding_Bonus_Points','Raiding_Self_Out_Points','Raiding_All_Out_Points'],
                'Raiding_Team_Points',
                label="Attacking Points"
            )
            check_points(
                ['Defending_Capture_Points','Defending_Bonus_Points','Defending_Self_Out_Points','Defending_All_Out_Points'],
                'Defending_Team_Points',
                label="Defensive Points"
            )

            # QC 9: Outcome == Successful/Unsuccessful must have points

            def check_points_nonzero(df, outcome, cols, team_name):
                outcome_mask = df['Outcome'].eq(outcome)
                zero_points = df[cols].fillna(0).sum(axis=1).eq(0)
                problem_mask = outcome_mask & zero_points
                if problem_mask.any():
                    for raid_no in df.loc[problem_mask, 'Event_Number'].astype(str):
                        print(f"❌ {team_name}: Raid {raid_no} — Outcome is '{outcome}', but no points were given.\n")
                else:
                    print(f"QC 9: ✅ All {team_name} ({outcome}) rows are correct.\n")

            check_points_nonzero(
                df, 'Successful',
                ['Raiding_Touch_Points', 'Raiding_Bonus_Points', 'Raiding_Self_Out_Points', 'Raiding_All_Out_Points'], 'Raiding'
            )
            check_points_nonzero(
                df, 'Unsuccessful',
                ['Defending_Capture_Points', 'Defending_Bonus_Points', 'Defending_Self_Out_Points', 'Defending_All_Out_Points'], 'Defending'
            )

            # QC 10: Defending_Self_Out_Points > 1

            mismatch = df['Defending_Self_Out_Points'] > 1
            if mismatch.any():
                for msg in "❌ " + df.loc[mismatch, 'Event_Number'].astype(str) + "  Check 'Raider self out'\n":
                    print(msg)
            else:
                print('QC 10: ✅ All rows are correct.\n')


            # QC 11: Raid_Length should be > 2
            errors_found = False
            
            for idx, row in df.iterrows():
                if row['Raid_Length'] <= 2:
                    print(f"⚠️ {row['Event_Number']}: Raid_Length is {row['Raid_Length']}\n")
                    errors_found = True
            if not errors_found:
                print("QC 11: ✅ All rows have valid Raid_Length values.\n")


            # QC 12: Number_of_Defenders should be > 0
            errors_found = False
            
            for idx, row in df.iterrows():
                if row['Number_of_Defenders'] <= 0:
                    print(f"❌ {row['Event_Number']}: Number_of_Defenders is --> {row['Number_of_Defenders']}, Check \n")
                    errors_found = True
            if not errors_found:
                print("QC 12: ✅ All rows have valid Number_of_Defenders values.\n")



            # QC 13: Successful, No Bonus, No Defenders Self Out all 3 skills 

            fil_df = df[
                (df['Outcome'] == 'Successful') &
                (df['Bonus'] == 'No') &
                (df['Number_of_Defenders_Self_Out'] == 0)
            ].copy()

            # Replace empty strings with NA
            for col in ['Attacking_Skill', 'Defensive_Skill', 'Counter_Action_Skill']:
                fil_df[col] = fil_df[col].replace('', pd.NA)

            # Existing conditions
            cond1 = (fil_df['Attacking_Skill'].isna() &
                    (fil_df['Defensive_Skill'].isna() | fil_df['Counter_Action_Skill'].isna()))
            cond2 = (fil_df['Attacking_Skill'].notna() &
                    (fil_df['Defensive_Skill'].notna() | fil_df['Counter_Action_Skill'].notna()))

            # New condition: all three skills empty
            cond_all_empty = (fil_df['Attacking_Skill'].isna() &
                            fil_df['Defensive_Skill'].isna() &
                            fil_df['Counter_Action_Skill'].isna())

            # Combine conditions for QC check
            qc_wrong_rows = fil_df.loc[cond1 | cond2, 'Event_Number']

            if not qc_wrong_rows.empty:
                for event in qc_wrong_rows:
                    print(f"⚠️ {event}: 'Attacking_Skill' & 'Defensive & Counter_Action_Skill' - all 3 Present Check once.\n")

            # Check for all three empty separately
            all_empty_rows = fil_df.loc[cond_all_empty, 'Event_Number']
            if not all_empty_rows.empty:
                for event in all_empty_rows:
                    print(f"❌ {event}: All three skill columns are empty. Please check.\n")

            # If neither issue exists
            if qc_wrong_rows.empty and all_empty_rows.empty:
                print("QC 13: ✅ All rows are correct.\n")

            
            # QC 14: Outcome = Unsuccessful -> Defensive_Skill must NOT be empty
            qc_violations = df[
                (df['Outcome'] == 'Unsuccessful') &
                (df['Defensive_Skill'].isna() | (df['Defensive_Skill'].str.strip() == ''))
            ]
            if not qc_violations.empty:
                for idx, row in qc_violations.iterrows():
                    print(f"❌ {row['Event_Number']}: Outcome is 'Unsuccessful' and 'Defensive_Skill' is empty.\n")
            else:
                print("QC 14: ✅ All rows are correct.\n")


            # QC 15: Outcome = Successful & Bonus = No -> Defensive_Skill & Counter_Action_Skill both must NOT be empty or both must be empty

            # Helper function (must be defined)
            def is_empty(cell):
                return pd.isna(cell) or str(cell).strip() == ''
            
            # Base filter
            mask = (df['Outcome'] == 'Successful') & (df['Bonus'] == 'No')
            
            # ADDED: Mandatory inclusion of the Raiding_Touch_Points condition
            mask &= (df['Raiding_Touch_Points'] > 0)
            
            filtered = df[mask]
            
            # Find violations where one column is empty but not the other
            violations = filtered[
                (filtered['Defensive_Skill'].apply(is_empty) & ~filtered['Counter_Action_Skill'].apply(is_empty)) |
                (~filtered['Defensive_Skill'].apply(is_empty) & filtered['Counter_Action_Skill'].apply(is_empty))]
            
            # Print results
            if not violations.empty:
                for idx, row in violations.iterrows():
                    print(f"❌ {row['Event_Number']}: 'Defensive_Skill' or 'Counter_Action_Skill' missing.\n")
            else:
                print(f"QC 15: ✅ All rows are correct.\n")


            # --- QC 16: Defender without Position & Position with Defenders---

            qc_failed_1 = df[(df["Defender_1_Name"].notna()) & (df["Defender_Position"].isna() | (df["Defender_Position"] == ""))]
            qc_failed_2 = df[(df["Defender_1_Name"].isna()) & (df["Defender_Position"].notna()) & (df["Defender_Position"] != "")]

            if qc_failed_1.empty and qc_failed_2.empty:
                print("QC 16: ✅ All defender-position mappings are consistent.\n")
            else:
                for event in qc_failed_1['Event_Number']:
                    print(f"❌ {event}: Defender(s) present but 'Defender_Position' is empty.\n")
                for event in qc_failed_2['Event_Number']:
                    print(f"❌ {event}: 'Defender_Position' present but Defender(s) is empty.\n")


            # --- QC 17: Defensive_Skill & QoD_Skill Alignment ---

            # Exclude specific values of Defensive_Skill
            excluded_skills = ["Defender self out", "Raider self out"]
            
            # Type 1: Defensive_Skill present (not excluded) but QoD_Skill missing
            qc_16_1 = df[
                (df["Outcome"] == "Unsuccessful") &
                (df["Defensive_Skill"].fillna("").str.strip() != "") &
                (~df["Defensive_Skill"].isin(excluded_skills)) &
                (df["QoD_Skill"].fillna("").str.strip() == "")
            ]
            
            # Type 2: QoD_Skill present but Defensive_Skill missing
            qc_16_2 = df[
                (df["Outcome"] == "Unsuccessful") &
                (df["QoD_Skill"].fillna("").str.strip() != "") &
                (df["Defensive_Skill"].fillna("").str.strip() == "")
            ]
            
            # Final check
            if qc_16_1.empty and qc_16_2.empty:
                print("QC 17: ✅ Defensive_Skill and QoD_Skill are aligned correctly.\n")
            else:
                if not qc_16_1.empty:
                    print(f"❌ [Type 1]: {qc_16_1['Event_Number'].tolist()} → Defensive_Skill present but QoD_Skill missing.\n")
                if not qc_16_2.empty:
                    print(f"❌ [Type 2]: {qc_16_2['Event_Number'].tolist()} → QoD_Skill present but Defensive_Skill missing.\n")


            # --- QC 18: Bonus & Type of Bonus ---

            # Normalize data
            df['Bonus'] = df['Bonus'].astype(str).str.strip().str.title()
            df['Type_of_Bonus'] = df['Type_of_Bonus'].astype(str).str.strip()
            
            # QC Conditions
            condition_1 = (df['Bonus'] == 'Yes') & ((df['Type_of_Bonus'] == '') | (df['Type_of_Bonus'].isnull()))
            condition_2 = (df['Bonus'] == 'No') & ((df['Type_of_Bonus'] != '') & (~df['Type_of_Bonus'].isnull()))
            
            # Combine failed rows
            failed_rows = df[condition_1 | condition_2]
            
            # If-Else with detailed print statements
            if failed_rows.empty:
                print("QC 18: ✅ All rows are correct!\n")
            else:
                for _, row in failed_rows.iterrows():
                    if row['Bonus'] == 'Yes' and (row['Type_of_Bonus'] == '' or pd.isnull(row['Type_of_Bonus'])):
                        print(f"❌ {row['Event_Number']}: Bonus is 'Yes' but Type_of_Bonus is missing or empty.\n")

                    elif row['Bonus'] == 'No' and (row['Type_of_Bonus'] != '' and not pd.isnull(row['Type_of_Bonus'])):
                        print(f"❌ {row['Event_Number']}: Bonus is 'No' but Type_of_Bonus should be null.\n")
                        

            # --- QC 19: When Outcome = 'Successful' or 'Unsuccessful', Zone_of_Action must not be empty ---

            # Filter rows where Outcome is 'Successful' or 'Unsuccessful'
            zone_mask = df['Outcome'].isin(['Successful', 'Unsuccessful'])
            
            # Check for empty Zone_of_Action in those rows (now handles NaN, empty strings, and whitespace)
            empty_zone = df[zone_mask & (df['Zone_of_Action'].isna() | (df['Zone_of_Action'].astype(str).str.strip() == ''))]
            
            if not empty_zone.empty:
                for _, row in empty_zone.iterrows():
                    print(f"❌ {row['Event_Number']}: →  Zone_of_Action is empty.\n")
            else:
                print(" QC 19: ✅ All rows meet conditions for Outcome = 'Successful' or 'Unsuccessful'.\n")


            # --- QC 20: When ['Defensive_Skill'] == 'Raider self out' these below 4 columns must be empty ---

            # Columns to check
            columns_to_check = ['QoD_Skill', 'Defender_1_Name', 'Defender_Position', 'Counter_Action_Skill']
            
            # Mask for rows where Defensive_Skill == 'Raider self out'
            mask = df['Defensive_Skill'] == 'Raider self out'
            
            # Skip rows where Attacking_Skill == 'Defender self out' AND Defensive_Skill == 'Raider self out'
            skip_mask = mask & (df['Attacking_Skill'] == 'Defender self out')
            
            # Apply mask excluding skipped rows
            check_mask = mask & ~skip_mask
            
            # Mask for rows violating the "all 4 must be empty" rule
            violations_mask = check_mask & df[columns_to_check].apply(lambda x: x.notna() & (x != ''), axis=1).any(axis=1)
            
            # Filter only the violated rows
            flagged = df[violations_mask]
            
            # Print results
            if not flagged.empty:
                for idx, row in flagged.iterrows():
                    # Identify which of the 4 columns have values
                    non_empty_cols = [col for col in columns_to_check if pd.notna(row[col]) and row[col] != '']
                    print(f"❌ {row['Event_Number']}: Found values in {', '.join(non_empty_cols)} — these must be empty when Defensive_Skill = 'Raider self out'.\n")

            else:
                print("QC 20: ✅ All rows are correct.\n")
                

            # --- QC 21: When Outcome = 'Successful', Bonus = 'Yes', and Raiding_Team_Points = 1, all skill columns must be empty. ---

            # Define the columns to check
            columns_to_check = ['Attacking_Skill', 'Defensive_Skill', 'QoD_Skill', 'Counter_Action_Skill']

            # Filter the DataFrame based on the given conditions
            filtered_df = df[
                (df['Outcome'] == 'Successful') &
                (df['Bonus'] == 'Yes') &
                (df['Raiding_Team_Points'] == 1)]

            # QC check
            issues_found = False

            for idx, row in filtered_df.iterrows():
                for col in columns_to_check:
                    # Treat empty strings as NaN
                    if not pd.Series([row[col]]).replace('', pd.NA).isna().iloc[0]:
                        print(
                            f"❌ {row['Event_Number']}: When Outcome='Successful', Bonus='Yes', and Raiding_Team_Points=1, "
                            f"all skill columns must be empty. But '{col}' has value '{row[col]}'.\n")
                        issues_found = True

            # Final message
            if not issues_found:
                print("QC 21: ✅ All rows are correct.\n")


           # --- QC 22 QoD_Skill & Outcome Alignment Check ---

            # --- 1. Define Boolean Masks ---
            # A value is considered "present" if the cell is not null, empty, or just whitespace.
            is_def_skill_present = df["Defensive_Skill"].fillna("").str.strip() != ""
            is_qod_skill_present = df["QoD_Skill"].fillna("").str.strip() != ""
            is_successful = df['Outcome'] == 'Successful'

            # --- 2. Identify All Potential Issues ---
            # Type 1: QoD_Skill is present, but Defensive_Skill is missing.
            type_1_issues = df[is_qod_skill_present & ~is_def_skill_present]

            # Type 2: Raid is Successful, but QoD_Skill is present.
            type_2_issues = df[is_successful & is_qod_skill_present]


            # --- 3. Unified Final Check & Reporting ---
            if type_1_issues.empty and type_2_issues.empty:
                print("QC 22: ✅ All skill and outcome alignments are correct.\n")
            else:
                # If any issues exist, report them specifically using the original messages.
                if not type_1_issues.empty:
                    print(f"❌ {type_1_issues['Event_Number'].tolist()} → QoD_Skill present but Defensive_Skill missing.\n")

                if not type_2_issues.empty:
                    print(f"❌ {type_2_issues['Event_Number'].tolist()} → Raid is Successful but QoD_Skill is present, should be None.\n")


# =========================================================================

            # Example: saving final processed dataframe
            df.to_csv(output_file_name, index=False)

            # Reset stdout back to default
            sys.stdout = sys.__stdout__

            # --- Show QC logs in scrollable box ---
            qc_text = log_output.getvalue()

            st.markdown(
                f"""
                <div style="height:400px; overflow-y:scroll; border:2px solid yellow;
                            border-radius:8px; padding:10px; background-color:#1E1E1E; color:white;">
                    <pre>{qc_text}</pre>
                </div>
                """,
                unsafe_allow_html=True)

            st.markdown("")
            st.markdown("")
            # --- Show Total Rows and Columns for PROCESSED file ---
            final_rows, final_cols = df.shape if df is not None else (0, 0)
            st.write(f"**Total rows:** `{final_rows}` | **Total columns:** `{final_cols}`")


            # Show first 5 rows of final CSV
            st.subheader("Processed File Preview")
            st.dataframe(df, height=210)

            # CSS to style the download button
            st.markdown(
            """
            <style>
            div.stDownloadButton>button {
                color: yellow !important;
                font-weight: bolder !important;
                font-size: 30px !important;  /* Increase font size */
                background-color: black !important;
                border: none !important;
                padding: 10px 20px !important; /* Makes button bigger */
            }
            </style>
            """,
            unsafe_allow_html=True)

            clean_match_id = match_id.lstrip("M")
            
            st.write(f"**File Name:** `tagged_{match_no}_{clean_match_id}.csv`")

            # Download button
            with open(output_file_name, "rb") as f:
                st.download_button(
                    label="Download Processed CSV",
                    data=f,
                    file_name=f"tagged_{match_no}_{clean_match_id}.csv",
                    mime="text/csv",
                    use_container_width=True)

        except Exception as e:
            sys.stdout = sys.__stdout__
            st.error(f"❌ An error occurred: {e}")







