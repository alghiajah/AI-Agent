import time
from app.services.strategist import StrategistAgent
from app.services.analyst import AnalystAgent
from app.services.communicator import CommunicatorAgent
from app.schemas.chat import ChatResponse, AgentStep


class AgentOrchestrator:
    """
    Orchestrates the three specialized agents sequentially:

    1. Strategist Agent (DeepSeek-V3)
       → Breaks down the user's question into a structured Investigation Brief.

    2. Analyst Agent (Gemini 2.5 Flash)
       → Performs deep technical analysis based on the Investigation Brief,
         producing a rich Technical Analysis Report.

    3. Communicator Agent (GPT-4o)
       → Transforms the raw analysis into a clear, engaging, and beautifully
         formatted Markdown response for the end user.
    """

    def __init__(self):
        self.strategist = StrategistAgent()
        self.analyst = AnalystAgent()
        self.communicator = CommunicatorAgent()

    async def run_chain(self, user_message: str, mode: str = "chain", session_id: str = None, username: str = "default") -> ChatResponse:
        """
        Runs the specialized multi-agent pipeline sequentially or invokes a single specialized agent.
        Tracks execution time per agent and in total.
        """
        import uuid
        if not session_id:
            session_id = f"session-{uuid.uuid4().hex}"

        steps = []
        start_total = time.perf_counter()

        if mode == "chain":
            # ── 1. Strategist Agent (DeepSeek-V3) ────────────────────────────────
            # Creates a structured Investigation Brief from the user's raw question.
            start_step = time.perf_counter()
            investigation_brief = await self.strategist.execute(user_message)
            
            # Deteksi off-topic
            if investigation_brief.strip() == "[OFFTOPIC]":
                final_response = "Maaf, sistem orkestrasi asisten AI ini didesain khusus hanya untuk melayani topik seputar Jaringan Telekomunikasi dan Teknologi Informasi. Silakan ajukan pertanyaan yang relevan dengan topik tersebut."
                steps.append(
                    AgentStep(
                        agent_name=self.strategist.name,
                        model_used=self.strategist.model,
                        output="Mendeteksi input di luar topik (Off-Topic). Menghentikan rantai kolaborasi lebih awal.",
                        execution_time_seconds=round(time.perf_counter() - start_step, 3),
                    )
                )
                total_execution_time = round(time.perf_counter() - start_total, 3)
                
                # Simpan ke riwayat database
                from app.services.history import add_chat
                add_chat(username, session_id, mode, user_message, final_response, steps)
                
                return ChatResponse(
                    status="success",
                    session_id=session_id,
                    user_message=user_message,
                    final_response=final_response,
                    steps=steps,
                    total_execution_time_seconds=total_execution_time,
                )

            steps.append(
                AgentStep(
                    agent_name=self.strategist.name,
                    model_used=self.strategist.model,
                    output=investigation_brief,
                    execution_time_seconds=round(time.perf_counter() - start_step, 3),
                )
            )

            # ── 2. Analyst Agent (Gemini 2.5 Flash) ──────────────────────────────
            # Performs deep technical analysis on the Investigation Brief.
            start_step = time.perf_counter()
            analysis_report = await self.analyst.execute(investigation_brief)
            steps.append(
                AgentStep(
                    agent_name=self.analyst.name,
                    model_used=self.analyst.model_name,
                    output=analysis_report,
                    execution_time_seconds=round(time.perf_counter() - start_step, 3),
                )
            )

            # ── 3. Communicator Agent (GPT-4o) ────────────────────────────────────
            # Transforms raw analysis into a polished, user-facing Markdown response.
            start_step = time.perf_counter()
            final_response = await self.communicator.execute(user_message, analysis_report)
            steps.append(
                AgentStep(
                    agent_name=self.communicator.name,
                    model_used=self.communicator.model,
                    output=final_response,
                    execution_time_seconds=round(time.perf_counter() - start_step, 3),
                )
            )
        elif mode == "gemini_network":
            from app.services.gemini_network import GeminiNetworkAgent
            agent = GeminiNetworkAgent()
            start_step = time.perf_counter()
            output = await agent.execute(user_message)
            steps.append(
                AgentStep(
                    agent_name=agent.name,
                    model_used=agent.model_name,
                    output=output,
                    execution_time_seconds=round(time.perf_counter() - start_step, 3),
                )
            )
            final_response = output
        elif mode == "gpt_math":
            from app.services.gpt_math import GptMathAgent
            agent = GptMathAgent()
            start_step = time.perf_counter()
            output = await agent.execute(user_message)
            steps.append(
                AgentStep(
                    agent_name=agent.name,
                    model_used=agent.model,
                    output=output,
                    execution_time_seconds=round(time.perf_counter() - start_step, 3),
                )
            )
            final_response = output
        elif mode == "deepseek_code":
            from app.services.deepseek_code import DeepseekCodeAgent
            agent = DeepseekCodeAgent()
            start_step = time.perf_counter()
            output = await agent.execute(user_message)
            steps.append(
                AgentStep(
                    agent_name=agent.name,
                    model_used=agent.model,
                    output=output,
                    execution_time_seconds=round(time.perf_counter() - start_step, 3),
                )
            )
            final_response = output
        else:
            raise ValueError(f"Mode tidak dikenal: {mode}")

        total_execution_time = round(time.perf_counter() - start_total, 3)

        # Simpan ke riwayat database
        from app.services.history import add_chat
        add_chat(username, session_id, mode, user_message, final_response, steps)

        return ChatResponse(
            status="success",
            session_id=session_id,
            user_message=user_message,
            final_response=final_response,
            steps=steps,
            total_execution_time_seconds=total_execution_time,
        )
