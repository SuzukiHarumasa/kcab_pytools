from typing import Union, List, Optional
import gspread
from gspread import Spreadsheet
import pandas as pd
import datetime
import webbrowser
from apiclient import discovery  # pip install google-api-python-client


class GSheets:
    def __init__(self, creds: str):
        """
        Inputs:
            - creds: the path to the credentials file for the Google Services Account.
        Attributes:
            - gc: google spreadsheet client. Use to get `gspread` convenience methods.
            - api: google api client using the apiclient.discovery module from `google-api-python-client`. Use for lower level configurations.
            - last_sheets_url: a url reference to the last processed Google Sheets.
        """
        self.creds = creds
        self.gc = gspread.service_account(filename=creds)
        self.api = discovery.build('drive', 'v3', credentials=self.gc.auth)
        self.last_sheets_url = None

    def save_df(self, df: pd.DataFrame, dest: str = "0BxpY8IQbguQWa3V5blloRWFjMzA", title="Untitled") -> Spreadsheet:
        """Saves the dataframe to the destination folder ID specified, and returns the resulting file object.
        The default destination is the "Rebase, Inc. Team" folder.
        Inputs:
            - df: dataframe to save to Google Drive.
            - dest: the folder where you want to save your Google Sheet.
            - title: the title of the Google Sheet.
        """

        # Convert NaN values to empty string so that Google Spreadsheet API can process it.
        df = df.fillna('')

        # Save dataframe to a new sheet
        sheets = self.gc.create(title)
        worksheet = sheets.get_worksheet(0)
        worksheet.update(self.df_to_rows(df))

        self.move_folder(sheets, dest)
        self.last_sheets_url = sheets.url

        return sheets

    def move_folder(self, sheets: Spreadsheet, dest: str) -> Spreadsheet:
        f = self.api.files().get(fileId=sheets.id, fields='parents').execute()
        prev_parents = ",".join(f.get('parents'))
        f = self.api.files().update(fileId=sheets.id,
                                    addParents=dest,
                                    removeParents=prev_parents,
                                    fields='id, parents').execute()
        return sheets

    def df_to_rows(self, df: pd.DataFrame, headers: bool = True) -> List[list]:
        """
        Converts data frame into list of lists.
        Inputs:
            - df: Data frame to convert into list of lists.
            - headers: whether to include column names.
        Returns:
            - Rows of data as list of lists.
        """
        if headers:
            return [df.columns.values.tolist()] + df.values.tolist()
        return df.values.tolist()

    def rows_to_df(self, rows: List[list], headers: bool = True) -> pd.DataFrame:
        "Returns data frame from rows using first row as column names if `headers` is `True`."
        # If rows are empty such as [], then return empty DataFrame.
        if not rows:
            return pd.DataFrame()

        # Otherwise, assume list of lists to contain headers in first row.
        df = pd.DataFrame(rows[1:])
        if headers:
            df.columns = rows[0]

        # Convert numeric columns to numeric values if possible
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')
        return df

    def append(self, df: pd.DataFrame, sheet: Spreadsheet) -> pd.DataFrame:
        "Append data frame data to the bottom of a given sheet."
        current_content = sheet.get_values(
            value_render_option='UNFORMATTED_VALUE')

        # If the spreadsheet is empty, just append the rows.
        if not current_content:
            sheet.append_rows(self.df_to_rows(df, headers=True))
            return df

        # Otherwise check if the columns align and append without column names if they do.
        headers = current_content[0]
        column_names_all_align = all([col == header
                                      for col, header in zip(df.columns.tolist(), headers)])

        if column_names_all_align:
            # If all of the columns names are the same, then skip adding the headers
            sheet.append_rows(self.df_to_rows(df, headers=False))
        else:
            # Otherwise, add the headers so that the data is understandable
            sheet.append_rows(self.df_to_rows(df, headers=True))

        # Get updated sheet content
        current_content = self.rows_to_df(sheet.get_values())
        return current_content

    def concat(self, df: pd.DataFrame, sheet: Spreadsheet) -> pd.DataFrame:
        "Concatenates `df` with existing content of `sheet`."
        current_content = self.rows_to_df(sheet.get_values(
            value_render_option='UNFORMATTED_VALUE'))
        updated_content = pd.concat([current_content, df], axis=0)
        self.update(sheet, updated_content)
        return updated_content

    def drop_duplicates(self, sheet: Spreadsheet, columns: Optional[list] = None) -> pd.DataFrame:
        "Drops duplicates from `sheet`."
        if isinstance(columns, str):
            columns = [columns]

        current_content = self.rows_to_df(sheet.get_values(
            value_render_option='UNFORMATTED_VALUE'))
        updated_content = current_content.drop_duplicates(columns, keep='last')
        self.update(sheet, updated_content)
        return updated_content

    def sort_values(self, sheet: Spreadsheet, column: str, ascending: bool = True) -> pd.DataFrame:
        "Sorts the spreadsheet by `column`."
        current_content = self.rows_to_df(sheet.get_values(
            value_render_option='UNFORMATTED_VALUE'))
        updated_content = current_content.sort_values(column, ascending=ascending)\
            .reset_index(drop=True)
        self.update(sheet, updated_content)
        return updated_content

    def update(self, sheet: Spreadsheet, df: pd.DataFrame) -> pd.DataFrame:
        "Updates given `sheet` with contents of `df`. Previous content is overwritten."
        sheet.clear()
        sheet.update(self.df_to_rows(df.fillna('')))
        return df

    def share(self, sheets: Spreadsheet, emails: Union[str, List[str]]) -> None:
        if not isinstance(emails, list):
            emails = [emails]

        for email in emails:
            sheets.share(email, perm_type='user', role='writer')

    def open(self, url: Optional[str] = None) -> None:
        "Opens a Google Sheets url."
        url = url or self.last_sheets_url
        if url:
            webbrowser.open(url)
        else:
            raise Exception(
                "No URL specified. Either supply a `url` to the function or process a spreadsheet first.")
