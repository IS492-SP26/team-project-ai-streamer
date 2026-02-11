# team-project-ai-streamer
team-project-ai-streamer created by GitHub Classroom
- Team Member - Danni Wu, Fitz Song, Caroline Wen
- AI VTuber Orchestrator, a generative AI system designed to make AI characters safer, more consistent, and more usable for real applications. Instead of creating another VTuber bot,  focus is more on building a product-level middleware that sits between an LLM and a live system.  Reference and inspied by Neuro sama agents.
The system may has two parts:
- An LLM-driven “director” that helps generate persona-consistent dialogue, plan topics, and shape AI character behavior in a controllable way.
- Guardrail & saftey layer: A real-time moderation layer that evaluates the AI’s generated text for toxicity, NSFW content, political sensitivity, or persona drift, and automatically rewrites or blocks unsafe output.
Goal: To create a plug-in SDK + small web console that any AI VTuber or LLM agent system (Unity/Python pipelines) can connect to via a simple API .

