# Import Parsing Tools
import requests
from bs4 import BeautifulSoup

# Import NLP Tools
from sumy.summarizers.luhn  import LuhnSummarizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer


# Import Utils
import numpy as np
import pickle


class equity_research_reports():
    """ Class to generate equity research reports for a given portfolio's constituents. This class will leverage the latest news articles sourced from FinViz to then formulate 
        a compressed summary of significant news. These reports will later be fed into ChatGPT3 for a generative summary and formal equity reserach report.
    """

    def __init__(self, tickers: np.array, n_articles = 10) -> None:
        """
        Args:
            tickers (np.array): Portfolio constituents.
            n_articles (int, optional): Number of articles to injest per stock. Defaults to 10.
        """
        self.tickers = tickers
        self.n_articles = n_articles
        self.equity_research_reports = self.get_equity_research_reports()

    def scrape(self, url: str) -> str:
        """ Generate a string that aggregates a news article's content. This has two ways of execution:

            1) If a Yahoo Finance "Continue Reading" gateway link is present.
            2) In the absence of a Yahoo Finance gateway.

            In either scenario, the ultimate goal of extracting all relevant content within a news article is acheived.

        Args:
            url (str):

        Returns:
            str: Article content.
        """


        # Send a GET request to the URL - this is Yahoo Finance gateway to the full article
        yahoo_gateway_response = requests.get(url, headers={'User-Agent': 'Custom'})

        # Check if the request was successful
        try:
            
            # Parse the HTML content of the page
            soup = BeautifulSoup(yahoo_gateway_response.content, 'html.parser')

            # Get full article link from <a class="link caas-button"> tag. This is a Yahoo Finance specific tag that contain the "Continue Reading" hyperlink.
            article_link = soup.find('a', class_ ='link caas-button')['href']
            
            # ------------------------------ Get Full Article Text ------------------------------

            # Send a GET request to the URL - this is the full article that news text will be extracted from
            article = requests.get(article_link, headers={'User-Agent': 'Custom'})

            # Check if the request was successful
            try:

                # Parse the HTML content of the page
                soup = BeautifulSoup(article.content, 'html.parser')

                # Get all <p> tags which contain the news article's text
                article_txt_iter = soup.find_all('p')

                # Initialize str to article's full text
                article_txt = ''

                # Iterate through <p> tags and store all information
                for txt in article_txt_iter:
                    article_txt += txt.text.strip()
                
                return article_txt

            except:
                print(f'Reponse Error - Final Article: {article.status_code}')
                print(f'Problem Link: {article_link}')

        except:

            # If the first method of traveling through a Yahooo Finance gateway doesn't work, this normally means the article was directly linked by FinViz. 
            # Therefore, try to extract text directly from the Yahoo link.
            try:
                # ------------------------------ Get Full Article Text - NO Yahoo Gateway ------------------------------

                # Send a GET request to the URL - this is the full article that news text will be extracted from
                article = requests.get(url, headers={'User-Agent': 'Custom'})

                # Check if the request was successful

                # Parse the HTML content of the page
                soup = BeautifulSoup(article.content, 'html.parser')

                # Get all <p> tags which contain the news article's text
                article_txt_iter = soup.find_all('p')

                # Initialize str to article's full text
                article_txt = ''

                # Iterate through <p> tags and store all information
                for txt in article_txt_iter:
                    article_txt += txt.text.strip()
                
                return article_txt
            
            except:
                print(f'Reponse Error - Yahoo Gateway: {yahoo_gateway_response.status_code}')
                print(f'Problem Link: {url}')
        
        return ''

    def get_stock_news(self, url: str, n_articles = 10) -> np.array:
        """ Pass a given stock's FinViz URL to this function to store all relevent news in a single string. 
            We initially leverage a FinViz URL which then takes us to a series of Yahoo Finance articles. 
            This is to circumvent Yahoo Finance's ads framework, making it easier to immediately get relevant information. 
            
            The workflow proceeds as follows:
            1) Initiate a GET request to the given URL and process the page's content with BeautifulSoup's html.parser.
            2) Iterate through all of FinViz's <div> tags that relate to news links. 
            3) For each relevant <div>, get all news links via each <a> tag's ['href'] value and store in np.array "links".
            4) Iterate through each link in "links" (np.array).
            5) For each link, Yahoo Finance has a "Continue Reading" button which contains the link to the final news article that must be parsed.
            6) Thus, we need to follow that link and extract all text from the body of the final article by iterating through each <p> tag within a particular <div>.
                    

        Args:
            url (str): 
            n_articles (int, optional): Number of articles to injest per stock. Defaults to 10.

        Returns:
            _type_: _description_
        """
        # Send a GET request to the URL
        # In this case, the site is filtering on the user agent, it looks like they are blacklisting Python, setting it to almost any other value already works:
        response = requests.get(url, headers={'User-Agent': 'Custom'})
        
        # Check if the request was successful
        if response.status_code == 200:

            # ------------------------ Scrape all news links from a given stock's FinViz page ------------------------ 

            # Parse the HTML content of the page
            soup = BeautifulSoup(response.content, 'html.parser')

            # Initialize np.array to store all news links from FinViz page
            links = np.array([])
            
            # Create an iterable object of all <div> tags that contain news links. This is a FinViz specific class. 
            div_iter = soup.find_all('div', class_ ='news-link-container')

            # Iterate through each div and append their respective news links in np.array
            for div in div_iter:
                # <a> tag indicates a link
                links_iter = div.find_all('a') 

                for a in links_iter:
                    links = np.append(links, a['href'])

            # ------------------------ Store a select list of article content from scraped URLs ------------------------ 

            # Initialize stock's np.array to store news content
            stock_news = np.array([])

            # Iterate through the all links on the stock's FinViz page
            for article in links:
                
                # Get article content
                tmp_article_text = self.scrape(article)
                
                # If the text has not already been added (i.e., a unique article has been parsed)
                if np.sum(np.isin(tmp_article_text, stock_news)) == 0:

                    print(article)
                    
                    # Store text
                    stock_news = np.append(stock_news, tmp_article_text)
                    
                    # Stop adding text if we have more than N articles recorded
                    if len(stock_news) == n_articles:
                        break

            return stock_news

        else:
            return None


    def compress_articles(self, stock_news: np.array, n_sentences=5) -> str:
        """ Compress and summarizes a np.array of news article content into a single string. This will be done with the extractive Luhn Summarization algorithm.
            Here, we can specify approximately how many sentences we want in the summary. If the summary is too long (according to ChatGPT3 max tokens), 
            decrease the number of sentences by 1 recursively until the token_size < max_token_size for ChatGPT3.


        Args:
            stock_news (np.array): Array of news article content (strings).
            n_sentences (int, optional): Number of sentences for the Luhn Summarization Algorithm. Defaults to 5.

        Returns:
            str: A given stock's compressed news summary.
        """

        article_summary = "" 

        for article in stock_news:

            parser = PlaintextParser.from_string(article, Tokenizer("english"))

            summarizer = LuhnSummarizer()

            # Summarize using sumy Luhn
            summary = summarizer(parser.document, n_sentences)

            for sentence in summary:
                article_summary += str(sentence)
                article_summary += '\n'
                                
        # Recursively call compress_articles function until a short-enough response is generated
        if len(article_summary.strip()) > 15000:
            
            return self.compress_articles(stock_news, n_sentences-1)
        
        # Print token count of newly compressed news content
        print(f'Compression Length {len(article_summary.strip())}')

        return article_summary



    def get_equity_research_reports(self) -> dict:
        """ Iterate through portfolio holdings, get their respective "self.n_articles" most recent news articles, compress the information via extractive NLP, and store in "portfolio_reports" dict.
            Each report will be the prompt for ChatGPT3 that can just be copy and pasted.

        Returns:
            dict: Dictionary {ticker : summary} 
        """

        equity_research_reports = {}

        for stock in self.tickers:
            
            print('=='*100)
            print(f'Getting report for {stock}:')

            prompt = f"You are a Wall Street fundamental stock portfolio manager and researcher who worked at both Citadel and Millennium, the hedge funds. You have a PhD in Mathematics and AI from MIT. Only using the following information, create a predictive stock market research report by extracting key financial/economic/business factors only from the following information to explain every factor that would impact {stock}'s stock price in the future and explain why these factors will dictate the companys price. Make sure there is an introduction and that it is a numerically listed report:"
            url = f'https://finviz.com/quote.ashx?t={stock}&p=d'

            # Store each news article content in np.array for a given stock
            stock_news = self.get_stock_news(url=url, n_articles=self.n_articles)

            # Compress and summarize all news articles into a single string
            prompt += self.compress_articles(stock_news=stock_news)
            
            # TO BE CLEAR: this is no the final equity research report, this is the prompt (queary + summarization of news) that is to be fed into ChatGPT3.
            equity_research_reports [stock] = prompt
        
        return equity_research_reports      


# Define portfolio constituents and generate compressed news summaries for each one that will act as prompts for ChatGPT3
tickers = ['FTAI', 'AMT', 'NEE', 'TDOC', 'INTC', 'FISV', 'DAL', 'ISRG', 'GOOS', 'TXN', 'TSM', 'MHK', 'ACLS', 'EPD', 'PLYM', 'ED']
equity_research_reports  = equity_research_reports(tickers).equity_research_reports 

# Pickle the research report prompts
path = r'portfolio_reports_1_31_22/chat_gpt_prompts.pickle'
with open(path, 'wb') as handler:
    pickle.dump(equity_research_reports, handler, protocol=pickle.HIGHEST_PROTOCOL) 

# Print out all reports for ease of copy/paste
for stock, report in equity_research_reports.items():
    print('=='*100)
    print(f'{stock} Report:')
    print(report)
    