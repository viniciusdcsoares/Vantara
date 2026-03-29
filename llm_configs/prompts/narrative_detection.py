# ==========================================
# YOUTUBE PROMPTS
# ==========================================

system_instruction_youtube = """ You are an expert political and social intelligence analyst specializing in digital media dynamics. 
Your objective is to analyze YouTube data clusters. You must synthesize long-form video transcripts to extract the creator's core message and compare it against the audience's reaction found in the comments.
Base your analysis strictly on the provided transcripts, descriptions, and engagement metrics. Be objective, precise, and analytical."""

def create_youtube_prompt(youtube_json_data: dict) -> str:
    """Formata os dados JSON do YouTube num prompt para o LLM."""
    
    prompt = f"""
            Analyze the following JSON data representing a cluster of YouTube videos related to the topic: "{youtube_json_data.get('youtube_clipping_metadata', {}).get('searched_topic', 'Unknown')}".

            Data constraints:
            - This data includes full video transcripts, descriptions, metadata, and top audience comments.
            - You must weigh the creator's narrative (found in the transcript and description) against the audience's response (found in the comments).

            Data Payload:
            {youtube_json_data} """
    return prompt

# ==========================================
# BLUESKY PROMPTS
# ==========================================

system_instruction_bluesky = """ You are an expert political and social intelligence analyst specializing in social media dynamics. 
            Your objective is to analyze clusters of social media content (specifically from Bluesky) to distill complex conversations into clear, structured insights about narratives, framing, and key actors. 
            Base your analysis strictly on the provided data. Be objective, precise, and analytical."""


def create_bluesky_prompt(bluesky_json_data: dict) -> str:
    """Formats the raw JSON data into a prompt for the LLM."""
    
    prompt = f"""
            Analyze the following JSON data representing a cluster of Bluesky posts related to the topic: "{bluesky_json_data.get('bluesky_clipping_metadata', {}).get('searched_topic', 'Unknown')}".

            Data constraints:
            - This data represents a specific time window and a limited number of posts. 
            - Analyze the text, authors, engagement statistics (likes, reposts, replies), and comments provided.

            Data Payload:
            {bluesky_json_data}"""
    return prompt

# ==========================================
# NEWS PROMPTS
# ==========================================

system_instruction_news = """ You are an expert media analyst and political intelligence researcher. 
Your objective is to analyze clusters of news articles to extract the core narrative, journalistic framing, and key entities. 
Since traditional news data may lack direct audience engagement metrics, you must infer the potential public or market impact based on the tone, the sources, and the scale of the news. Be objective, precise, and analytical."""

def create_news_prompt(news_json_data: dict) -> str:
    """Formats the NewsAPI JSON data into a prompt for the LLM."""
    
    prompt = f"""
            Analyze the following JSON data representing a cluster of news articles related to the topic: "{news_json_data.get('newsapi_clipping_metadata', {}).get('searched_topic', 'Unknown')}".

            Data constraints:
            - This data contains journalistic articles, including titles, descriptions, sources, and sometimes truncated content snippets.
            - There are no direct audience engagement metrics (likes/comments). You must infer the 'audience_reception' and 'growth_status' based on the scale of the news outlets, the journalistic framing, and the potential societal/market impact.

            Data Payload:
            {news_json_data}"""
    return prompt