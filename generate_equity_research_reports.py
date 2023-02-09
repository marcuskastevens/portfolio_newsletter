from fpdf import FPDF
import datetime as dt
import pickle

"""
Workflow:

1) Inherit FPDF class from library and overwrite footer method.
2) Load pickled ChatGPT3 prompts to get ticker list of current portfolio
3) Write {ticker}.txt into formated pdf.
4) Do this for each stock.

"""


# Leverage polymorphism / inheritance to overwrite the footer method in FPDF class
class PDF(FPDF):    

    def __init__(self) -> None:
        super().__init__()        

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Courier italic 8
        self.set_font('Courier', 'I', 8)
        # Text color in gray
        self.set_text_color(0)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')


# Load all ChatGPT prompts from pickled dict to get portfolio constituents
directory = 'portfolio_reports_2-7-23'
path = fr'{directory}/chat_gpt_prompts.pickle'

with open(path, 'rb') as handler:
    prompts = pickle.load(handler)

# Get portfolio holdings' tickers
tickers = prompts.keys()

# Load PDF class (inhereted original FPDF but utilized polymorphism to set footer)
pdf = PDF()

# Iterate through tickers to generate pdfs
for stock in tickers:

    with open(fr"{directory}/{stock}.txt", "r") as file:

        # Add a page
        pdf.add_page()

        # Read the contents of the txt file which contains the copied ChatGPT3 output
        report_txt = file.read().encode('latin-1', 'replace').decode('latin-1')

        date = dt.date.today()
        title = f'TAMID Equity Research Report {date}: {stock}'
        
        # Use Logo for Header
        image_w = 40
        image_h = 30
        pdf.image('TAMID Miami Logo.png', x = 210/2 - image_w/2, y = 10, w = image_w, h = image_h)
        # Line break
        pdf.ln(30)

        # Set title font and formatting
        pdf.set_font('Courier', 'B', 12)
        # Calculate width of title and position
        w = pdf.get_string_width(title) + 6
        pdf.set_x((210 - w) / 2)
        # Colors of frame, background and text
        pdf.set_fill_color(255, 255, 255)
        # Title
        pdf.cell(w, 9, title, 'FJ', 1)
        # Line break
        pdf.ln(10)
        
        # Set style and size of font that you want in the body of the report
        pdf.set_font("Courier", size = 10)        
        
        # Define width height, and justification of each line
        pdf.multi_cell(190, 10, txt = report_txt, align='FJ')

        # -------------------------------------- Use this line if you want individual PDFs --------------------------------------
        # # save the pdf with name .pdf
        # pdf.output(fr"{stock}_report.pdf")

# save the pdf with name .pdf
pdf.output(fr"{directory}/equity_research_reports_{date}.pdf")
#pdf.output(fr"portfolio_reports_1-31-23/equity_research_reports_{tickers[0]}_{date}.pdf")