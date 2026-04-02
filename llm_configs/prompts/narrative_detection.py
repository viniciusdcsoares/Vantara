# ==========================================
# YOUTUBE PROMPTS
# ==========================================

system_instruction_youtube = """ You are an expert political and social intelligence analyst specializing in digital media dynamics. 
Your objective is to analyze YouTube data clusters. You must synthesize long-form video transcripts to extract the creator's core message and compare it against the audience's reaction found in the comments.
Base your analysis strictly on the provided transcripts, descriptions, and engagement metrics. Be objective, precise, and analytical."""

CLAIM_EXTRACTION_GUIDANCE = """
            Claim classification rules:
            - Use claim_type = factual only when the central claim can be stated mainly as a descriptive or reportable assertion, without a material normative judgment, recommendation, or advocacy component.
            - Use claim_type = mixed when the item combines a concrete factual core with a central interpretive, evaluative, or normative position.
            - Use claim_type = argumentative when the central claim is primarily a position, interpretation, recommendation, or normative judgment, and any factual content mainly serves as support.
            - When in doubt between factual and mixed, choose mixed if the item's main takeaway depends on a value judgment, causal interpretation, or policy stance.

            Extraction rules:
            - factual_claim should capture the shortest useful factual proposition that anchors the item.
            - argument_claim_canonical should be one short proposition, clearly comparable across items, preserving the core position and frame while reducing slogans, insults, campaign language, and excess rhetoric.
            - argument_claim_raw should preserve the argument as it appears in the content with minimal intervention, only removing obvious transcription noise or unnecessary repetition.
            - Do not let argument_claim_canonical become a vague euphemism.
            - Do not let argument_claim_raw become a messy copy of the source text.
"""

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

def create_youtube_single_prompt(video_json_data: dict, topic: str) -> str:
    """Formats a single YouTube item into a prompt for the LLM."""

    prompt = f"""
            Analyze the following single YouTube video related to the topic: "{topic}".

            Data constraints:
            - This is a single item, not a full cluster.
            - Extract the item's core narrative and dominant framing based only on the provided data.
            - Return a short canonical claim in one sentence whenever possible.
            - Classify the main claim as factual, argumentative, or mixed.
            - Return a factual_claim whenever the item contains a concrete factual assertion.
            - Return argument_claim_canonical when the item contains an argumentative position.
            - argument_claim_canonical must preserve the central position and frame while reducing slogans, insults, campaign language, and excess rhetoric.
            - Return argument_claim_raw when the item contains an argumentative position.
            - argument_claim_raw must preserve the original argumentative formulation with minimal intervention, cleaning only obvious noise or redundancy.
            - Do not turn argument_claim_canonical into a euphemistic or generic paraphrase.
            - Do not make argument_claim_raw a disorganized copy of the original transcript.
            {CLAIM_EXTRACTION_GUIDANCE}

            Data Payload:
            {video_json_data} """
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

def create_bluesky_single_prompt(post_json_data: dict, topic: str) -> str:
    """Formats a single Bluesky item into a prompt for the LLM."""

    prompt = f"""
            Analyze the following single Bluesky post related to the topic: "{topic}".

            Data constraints:
            - This is a single item, not a full cluster.
            - Extract the item's core narrative and dominant framing based only on the provided data.
            - Return a short canonical claim in one sentence whenever possible.
            - Classify the main claim as factual, argumentative, or mixed.
            - Return a factual_claim whenever the item contains a concrete factual assertion.
            - Return argument_claim_canonical when the item contains an argumentative position.
            - argument_claim_canonical must preserve the central position and frame while reducing slogans, insults, campaign language, and excess rhetoric.
            - Return argument_claim_raw when the item contains an argumentative position.
            - argument_claim_raw must preserve the original argumentative formulation with minimal intervention, cleaning only obvious noise or redundancy.
            - Do not turn argument_claim_canonical into a euphemistic or generic paraphrase.
            - Do not make argument_claim_raw a disorganized copy of the original post.
            {CLAIM_EXTRACTION_GUIDANCE}

            Data Payload:
            {post_json_data}"""
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

def create_news_single_prompt(article_json_data: dict, topic: str) -> str:
    """Formats a single News item into a prompt for the LLM."""

    prompt = f"""
            Analyze the following single news article related to the topic: "{topic}".

            Data constraints:
            - This is a single item, not a full cluster.
            - Extract the item's core narrative and journalistic framing based only on the provided data.
            - Return a short canonical claim in one sentence whenever possible.
            - Classify the main claim as factual, argumentative, or mixed.
            - Return a factual_claim whenever the item contains a concrete factual assertion.
            - Return argument_claim_canonical when the article advances or implies an argumentative position.
            - argument_claim_canonical must preserve the central position and frame while reducing slogans, insults, campaign language, and excess rhetoric.
            - Return argument_claim_raw when the article advances or implies an argumentative position.
            - argument_claim_raw must preserve the original argumentative formulation with minimal intervention, cleaning only obvious noise or redundancy.
            - Do not turn argument_claim_canonical into a euphemistic or generic paraphrase.
            - Do not make argument_claim_raw a disorganized copy of the article.
            {CLAIM_EXTRACTION_GUIDANCE}

            Data Payload:
            {article_json_data}"""
    return prompt
