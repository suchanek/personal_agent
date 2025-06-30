# Personal Facts for Personal Agent Knowledge Base

This directory contains structured personal facts that can be fed to your Personal Agent through the Streamlit interface to build its knowledge base about you.

## Files Created

1. **`eric_structured_facts.txt`** - Complete list of all personal facts organized by category
2. **`send_facts_helper.py`** - Python script to help organize and format facts for sending to the agent
3. **`auto_send_facts.py`** - Automated script that directly sends facts to the agent and monitors success
4. **`eric_facts.json`** - Original JSON data with all personal information

## How to Use

### Method 1: Using the Helper Script

The helper script makes it easy to send facts in organized batches:

```bash
# See all available categories
python send_facts_helper.py list

# Send ALL facts at once
python send_facts_helper.py all

# Get facts from a specific category
python send_facts_helper.py basic_info

# Combine multiple categories
python send_facts_helper.py batch basic_info education technical_skills
```

### Method 2: Automated Script (Recommended)

The automated script directly sends facts to the agent and monitors for success:

```bash
# Send essential facts (basic_info, professional_identity, education)
python auto_send_facts.py

# Send ALL facts automatically
python auto_send_facts.py all

# Test run with basic facts only
python auto_send_facts.py test

# Send specific categories
python auto_send_facts.py basic_info education technical_skills
```

This script will:
- Initialize the Personal Agent directly
- Send facts in batches to avoid overwhelming the system
- Monitor response times and success rates
- Verify facts are stored in memory
- Test fact recall with sample questions
- Provide detailed progress reports

### Method 3: Manual Copy-Paste

1. Open `eric_structured_facts.txt`
2. Copy sections of facts you want to send
3. Paste them into the Streamlit chat interface

## Recommended Sending Strategy

### Option 1: Send All Facts at Once (Quick Setup)
```bash
python send_facts_helper.py all
```
This generates one large message with ALL your personal facts organized by category. Copy and paste the entire output into the Streamlit chat to quickly build your complete knowledge base.

### Option 2: Send Facts Gradually (Recommended for Better Processing)
To build your agent's knowledge base effectively, send facts in logical groups:

#### Session 1: Basic Identity
```bash
python send_facts_helper.py batch basic_info professional_identity
```

#### Session 2: Background & Skills
```bash
python send_facts_helper.py batch education technical_skills
```

#### Session 3: Work Experience
```bash
python send_facts_helper.py batch current_work major_achievements
```

#### Session 4: Additional Details
Send remaining categories as needed for specific conversations.

## Using with the Streamlit Agent

1. Start your Personal Agent Streamlit app:
   ```bash
   cd tools
   python paga_streamlit_agno.py
   ```

2. In the chat interface, paste the formatted facts from the helper script

3. The agent will automatically store these facts in its semantic memory system

4. You can verify the facts were stored by using the "Show All Memories" button in the sidebar

## Example Chat Messages

Here are some example messages you can send to the agent:

**Basic Info:**
```
Please remember these facts about me:

• My name is Eric G. Suchanek.
• I have a Ph.D. degree.
• I live at 4264 Meadow Creek CT Liberty TWP, OH 45011.
• My phone number is 513-593-4522.
• My email address is suchanek@mac.com.
• My GitHub profile is https://github.com/suchanek/.
• I am currently working on proteusPy at https://github.com/suchanek/proteusPy/.
```

**Professional Identity:**
```
Please remember these facts about me:

• I am a highly-skilled scientist seeking employment in computational chemistry, computational biology or Artificial Intelligence.
• I have broad experience in life science, computer systems, troubleshooting and customer service.
• I have management experience in a Fortune 50 company.
• I am currently working in structural biophysics, building proteusPy.
```

## Categories Available

- **basic_info** - Name, contact info, current project
- **professional_identity** - Career focus and experience summary
- **education** - Academic background and achievements
- **technical_skills** - Programming languages, tools, certifications
- **current_work** - Current positions and responsibilities
- **major_achievements** - Key accomplishments and innovations

## Tips for Best Results

1. **Send facts gradually** - Don't overwhelm the agent with all facts at once
2. **Use natural language** - The facts are written as first-person statements
3. **Verify storage** - Use the "Show All Memories" feature to confirm facts were stored
4. **Test recall** - Ask the agent questions about yourself to test memory recall
5. **Update as needed** - Send new facts or corrections as your situation changes

## Memory Management

The agent's memory system will:
- Store facts as semantic memories
- Associate related facts together
- Enable search and retrieval during conversations
- Maintain context across chat sessions

You can manage memories using the sidebar controls:
- **Show All Memories** - View stored facts
- **Search Memories** - Find specific information
- **Reset User Memory** - Clear all stored facts (use with caution)

## Next Steps

After loading your facts:
1. Test the agent's knowledge by asking questions about yourself
2. Have natural conversations and see how it uses your personal context
3. Add new facts as needed for specific topics or projects
4. Use the memory search to find specific information when needed
