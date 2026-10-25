"""Servidor MCP do radar: oferece as tools para qualquer cliente MCP (o agente do ADK, o Claude Desktop...).

Rodar: python -m radar_estagio.mcp_server
Ele fala por stdio, então não dá para conversar com ele no terminal: quem conecta é o cliente MCP.
Nas tools, nada pode dar print: no stdio a saída do programa é o próprio protocolo, e um print o corrompe.
"""
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

from .tools import analisar_vaga, buscar_vagas, listar_vagas_salvas

load_dotenv(Path(__file__).parent / ".env")  # o servidor é outro processo: o ADK não carrega as chaves (Gemini, SerpApi) para ele

servidor = MCPServer("radar-de-estagio")
for tool in (buscar_vagas, listar_vagas_salvas, analisar_vaga):
    servidor.add_tool(tool)  # o nome, a docstring e os tipos da função viram a descrição da tool

if __name__ == "__main__":
    servidor.run()  # stdio
