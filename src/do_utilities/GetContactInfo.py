from json import loads

from numpy import nan

# library for fuzzy string comparison, https://github.com/maxbachmann/rapidfuzz
from rapidfuzz import process

try:
    from do_utilities.Common import convertDistrictKids, cleanText
    from do_utilities.QueryDataWarehouse import getDataForLastXWeeks
except:
    from Common import convertDistrictKids, cleanText
    from QueryDataWarehouse import getDataForLastXWeeks


def findClosestIDForNames(database, name, school, cur_id):
    name = cleanText(name)

    if school == school and school != "":
        local_database = database[database["school"] == school]
    else:
        local_database = database
    all_names = local_database["standardName"]
    match = process.extractOne(name, all_names, processor=None, score_cutoff=90)

    if match:
        return database.iloc[match[2]]["student_id"]

    return cur_id


# Reads the current normal student report and converts it into a modified format for matching
def getFinalReport():
    # Get the basic student report
    database = getDataForLastXWeeks(6, "students")

    # Filter out all of the unenrolled students
    database = database[database["Status"] == "Active"]
    database.dropna(subset=['FirstName', "LastName"], inplace = True)

    # Rename some columns to their expected names
    database = database.rename(
        columns={"SchoolName": "school", "ID": "student_id", "Phones": "phone", "Program": "program"}
    )

    # Add in phone numbers, standard names, and schools
    database["phone"] = [extractContactNumbers(x) for x in database["phone"]]
    database["standardName"] = ""
    database["standardName"] = [
        cleanText(" ".join(" ".join([x, y]).split())) for x, y in zip(database["FirstName"], database["LastName"])
    ]
    database["schoolGroup"] = [convertDistrictKids(x) for x in database["school"]]

    # Filter df to only needed columns and save locally
    database = database[["school", "schoolGroup", "student_id", "standardName", "phone", "program"]]

    return database.reset_index(drop=True)


# Extract all of the phone numbers from the student report
def extractContactNumbers(row):
    # Create array to hold all found numbers
    numbers = []
    try:
        # parse the json elements in the row
        test = loads(row)

        for entry in test:

            # If the user hasn't opted out use add their number, else move on
            if entry["opt_out_communication"]:
                numbers.append(nan)
            else:
                # Ignore NAN
                if entry["number"] != entry["number"]:
                    continue

                # Expected length is 12, "+1" and 10 digit phone number
                if len(entry["number"]) == 11 and entry[:2] != "+1":
                    print(
                        "This number does not have the expected number of digits +1(10 digits)",
                        entry["number"],
                        "but I converted it to",
                        ("+1" + entry["number"][1:]),
                    )

                    # Number is typically missing the '+' or the '1', fixed both issues
                    entry["number"] = "+1" + entry["number"][1:]

                # If the number has any other issues
                if len(entry["number"]) != 12:

                    # Some numbers have a trailing zero added to them, if so add the phone numbers
                    # without it
                    if len(entry["number"]) == 13 and entry["number"][0] == "+" and entry["number"][12] == "0":
                        numbers.append((entry["number"][:-1]))
                        continue
                    continue

                # Add the current number to the array
                numbers.append(entry["number"])

        # Return the array of phone numbers
        return numbers
    except Exception:
        # Return NAN because the numbers could not be processed
        return nan


# Get a student's info from their ID
def getMissingInfoForEntry(df, id_col, name_col, school_col, program_col):
    # Get the database of known students and organize them by id
    database = getFinalReport()
    database = database.sort_values(by=["student_id"]).reset_index(drop=True)

    # missing_id_entries = df[df[id_col] != df[id_col]]

    for index, row in df.iterrows():
        df.loc[index, id_col] = findClosestIDForNames(database, row[name_col], row[school_col], row[id_col])

    # Group the master df by the id column to avoid duplicate checks for the same student
    df2 = df.groupby(id_col)

    # Iterate through each id and the entries associated with them
    for group, rows in df2:
        # Ignore empty ids
        if group in ["", " "]:
            # print(f"Failed to find ID for {len(rows)} students")
            continue

        # Filter the student report to just entries for this id
        try:
            database_for_id = database[database["student_id"] == group]
        except Exception:
            # There was no entry found for this student, move on
            continue

        # There was no entry found for this student, move on
        if database_for_id.empty:
            continue

        # Get a database values for this ID
        try:
            name = database_for_id["standardName"].unique()[0]
            school = database_for_id["school"].unique()[0]
            program = database_for_id["program"].unique()[0]
        except Exception:
            print(f"Failed to find name, school, and program for {group}")
            name = ""
            school = ""
            program = ""

        # Assign the values to the df from the database for the given ID
        df.loc[df[id_col] == group, name_col] = name
        df.loc[df[id_col] == group, school_col] = school
        df.loc[df[id_col] == group, program_col] = program
    return df
