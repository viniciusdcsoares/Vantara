from pydantic import BaseModel, Field
from typing import List
from enum import Enum

# ==========================================
# GENERAL PURPOSE SCHEMAS
# ==========================================

class GrowthStatus(str, Enum):
    GROWING = "growing"
    STABLE = "stable"
    DECLINING = "declining"
    UNCLEAR = "unclear"

class KeyActor(BaseModel):
    handle: str = Field(description="The Bluesky handle of the actor (e.g., nucleo.jor.br)")
    role: str = Field(description="The actor's apparent role (e.g., Journalist, Citizen, Politician, News Outlet)")
    stance: str = Field(description="The actor's stance on the core narrative (e.g., Supportive, Critical, Neutral)")

# ==========================================
# YOUTUBE SCHEMAS
# ==========================================

class YoutubeAnalysis(BaseModel):
    core_narrative: str = Field(
        description="A concise summary of the primary narrative found in the video transcripts and descriptions."
    )
    dominant_framing: str = Field(
        description="How the issue is framed by the creators (e.g., educational, alarmist, economic analysis)."
    )
    key_actors: List[KeyActor] = Field(
        description="List of the most influential actors, including the channel hosts, guests, and prominent commenters."
    )
    audience_reception: str = Field(
        description="Analysis of the 'most_liked_comments'. Does the audience agree, disagree, or expand on the video's premise?"
    )
    engagement_analysis: str = Field(
        description="Brief analysis of views, likes, and comment volume to determine the narrative's reach and impact."
    )
    growth_status: GrowthStatus = Field(
        description="Assessment of whether this topic/narrative appears to be growing, stable, or fading based on engagement."
    )
    notable_quotes: List[str] = Field(
        description="1-2 direct quotes (from the transcript OR the comments) that perfectly encapsulate the discussion."
    )

# ==========================================
# BLUESKY SCHEMAS
# ==========================================

class BlueskyAnalysis(BaseModel):
    core_narrative: str = Field(
        description="A concise summary of the primary narrative or discussion point found in the content cluster."
    )
    dominant_framing: str = Field(
        description="How the issue is being framed (e.g., as a regulatory issue, a moral panic, a technological advancement)."
    )
    key_actors: List[KeyActor] = Field(
        description="List of the most influential or representative actors driving the narrative in this cluster."
    )
    engagement_analysis: str = Field(
        description="Brief analysis of how engagement metrics (likes, reposts, comments) reflect the narrative's resonance."
    )
    growth_status: GrowthStatus = Field(
        description="Assessment of whether the narrative appears to be gaining traction, stable, or fading."
    )
    notable_quotes: List[str] = Field(
        description="1-2 direct quotes from the provided content that perfectly encapsulate the core narrative."
    )

# ==========================================
# NEWS SCHEMAS
# ==========================================

class ArticleTone(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    ALARMIST = "alarmist"
    SENSATIONALIST = "sensationalist"

class EntityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    GOVERNMENT = "government"
    PRODUCT_OR_TECH = "product_or_tech"

class NewsEntity(BaseModel):
    name: str = Field(description="Name of the person, company, or organization mentioned.")
    entity_type: EntityType = Field(description="The category of this entity.")
    context_role: str = Field(description="How this entity is portrayed in the news (e.g., 'Innovator', 'Regulator', 'Target of criticism').")

class NewsAnalysis(BaseModel):
    core_narrative: str = Field(
        description="A concise summary of the primary journalistic narrative across the articles."
    )
    journalistic_framing: str = Field(
        description="The angle the media is taking (e.g., economic opportunity, regulatory warning, technological breakthrough)."
    )
    overall_tone: ArticleTone = Field(
        description="The dominant editorial tone across the analyzed articles."
    )
    key_entities: List[NewsEntity] = Field(
        description="The main people, companies, or governments driving the news cycle in this cluster."
    )
    inferred_impact: str = Field(
        description="Since there are no comments, infer the potential impact of this news on public opinion, markets, or politics."
    )
    media_sources_analysis: str = Field(
        description="A brief note on the sources themselves (e.g., 'Tech and financial portals focusing on market growth')."
    )
    notable_quotes: List[str] = Field(
        description="1-2 direct quotes or powerful headlines extracted from the articles."
    )