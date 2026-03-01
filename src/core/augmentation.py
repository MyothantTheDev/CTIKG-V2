import os
from google import genai
from google.genai import types
from typing import List, Dict
from pydantic import BaseModel

class CTITriple(BaseModel):
  head: str
  head_type: str
  relationship: str
  tail: str
  tail_type: str

class CTIResponse(BaseModel):
  cot: str
  triples: List[CTITriple]

class DataGenerator:

  def __init__(self):
    api_key = os.getenv('API_KEY')
    if not api_key:
      raise ValueError("API_KEY not found in environment variables")
    self.client = genai.Client(api_key=api_key)
    

  def convert_cot_dataset(self, text: str, expected_output: str = None) -> Dict:
    
    instruction = """
    ### SYSTEM ROLE
    You are a Senior Cyber Threat Intelligence (CTI) Analyst and Knowledge Graph Engineer.
    Your task is to extract structured **Knowledge Graph Triples** from the provided CTI report text (or OCR output).
    """

    rules = """
    ### OBJECTIVE
    Convert unstructured text into a list of triples in the format: `(Subject, Relation, Object)`.
    The output must be strictly JSON format.

    ### 1. ENTITY TYPES (Subject/Object)
    Classify entities into these specific types. Do not invent new types.
    - **Threat_Actor**: (e.g., APT29, LockBit, Lapsus$)
    - **Malware**: (e.g., Cobalt Strike, Mimikatz, WannaCry)
    - **Infrastructure**: (e.g., 192.168.1.5, bad-domain.com, C2 Server)
    - **Vulnerability**: (e.g., CVE-2023-1234, Log4Shell)
    - **Tool**: (e.g., n8n, PowerShell, curl)
    - **Indicator**: (e.g., "uid=1000(node)", specific file hash)
    - **Victim**: (e.g., TechCorp, Finance Sector, Database)
    - **Location**: (e.g., /var/www/html, Output Panel)

    ### 2. ALLOWED RELATIONS (Predicates)
    Use ONLY the following relationships. Do not use generic verbs like "is" or "has".
    - `uses` (e.g., Actor uses Malware)
    - `targets` (e.g., Malware targets Victim)
    - `communicates_with` (e.g., Malware communicates_with Infrastructure)
    - `exploits` (e.g., Tool exploits Vulnerability)
    - `drops` (e.g., Malware drops File)
    - `indicates` (e.g., String indicates Command Injection)
    - `located_at` (e.g., File located_at Path)
    - `variant_of` (e.g., LockBit 3.0 variant_of LockBit)
    - `executes` (e.g., LNK file executes BAT script)

    ### 3. STRICT RULES (Must Follow)
    1. **Atomicity:** Entities must be atomic.
      - BAD: "malicious C2 server at 192.168.1.1"
      - GOOD: ("192.168.1.1", "is_type", "C2 Server")
    2. **Standardization:**
      - Normalize IPs and Domains (remove brackets like [.]).
      - Use canonical names (e.g., use "LockBit" instead of "LockBit Ransomware" unless version differs).
    3. **No Hallucination:** Only extract relationships explicitly stated or visually confirmed in the text.
    4. **Directionality:** Always follow: Active Entity -> Passive Entity.
      - Correct: `Attacker` -> `targets` -> `Victim`
      - Incorrect: `Victim` -> `targeted_by` -> `Attacker`
    5. **Technical Precision:**
      - If text says `uid=1000(node)`, extract it as an `Indicator` entity.
      - Relationship: ("uid=1000(node)", "indicates", "Command Injection")

    ### 4. CHAIN OF THOUGHT PROCESS (Internal Reasoning)
    Before generating the final JSON, perform the following steps internally:
    1.  **Identify Entities:** Scan the text for potential entities and assign them one of the allowed Types. (e.g., "Found '10.0.0.5', type: Infrastructure").
    2.  **Determine Relations:** For each pair of entities, check if a relationship exists based on the Allowed Relations list. Verify the direction (Source -> Target).
    3.  **Refine & Filter:**
        - Check against Strict Rules (Atomicity, Standardization).
        - Remove any inferred relationships not explicitly in the text.
        - Ensure predicates are from the allowed list only.

    ### 5. OUTPUT FORMAT (JSON)
    Return a JSON object with a key "triples".
    """

    try:
      instruction = f"{instruction}\n{rules}"
      response = self._generate_content(instruction, text, expected_output)

      if response.parsed:
        name_entities = []
        relationships = []

        for cti in response.parsed.triples:
          ne = [f"({cti.head}, {cti.head_type})", f"({cti.tail}, {cti.tail_type})"]
          rl = f"({cti.head}, {cti.relationship}, {cti.tail})"

          name_entities.append(ne)
          relationships.append(rl)
        
        return {
          'cot': response.parsed.cot,
          # 'triples': response.parsed.triples,
          # 'triples_count': len(response.parsed.triples)
          'name_entities': name_entities,
          'relationships': relationships
        }
      
      return ""
    
    except Exception as e:
      print(f"Error generating rationale: {e}")
      return ""
    
  def _generate_content(self, instruction: str, prompt: str, expected_output: str = None):

    expected_output = expected_output or """
    Example Input:
    "The LockBit 3.0 ransomware, executed by the affiliate using PowerShell, encrypted the Finance Server at 10.0.0.5."

    Example Output:
    ```json
    {
      "triples": [
      {"head": "LockBit 3.0", "type": "Malware", "relation": "uses", "tail": "PowerShell", "tail_type": "Tool"},
      {"head": "LockBit 3.0", "type": "Malware", "relation": "targets", "tail": "Finance Server", "tail_type": "Victim"},
      {"head": "Finance Server", "type": "Victim", "relation": "located_at", "tail": "10.0.0.5", "tail_type": "Infrastructure"}
      ]
    }
    """
    content = f"{prompt}\n{expected_output}"
    generate_content = self.client.models.generate_content(
      model="gemini-2.5-flash",
      config=types.GenerateContentConfig(
        system_instruction=instruction,

        temperature=0.1,
        top_p=0.95,
        max_output_tokens=8192,

        response_mime_type="application/json",
        response_schema=CTIResponse
      ),

      contents=content
    )

    return generate_content