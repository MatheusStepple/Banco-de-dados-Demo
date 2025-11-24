import psycopg2
import pandas as pd
import sys
import io
from datetime import datetime
import os

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ==============================================================================
# CONFIGURAÇÃO DA CONEXÃO
# ==============================================================================
DB_URL = "postgresql://postgres:CINBD2025@db.bvhcqxktyriytcmpsdln.supabase.co:5432/postgres"

# ==============================================================================
# FUNÇÕES DE CONEXÃO
# ==============================================================================
def conectar_banco():
    """Estabelece conexão com o banco de dados"""
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return None

# ==============================================================================
# RELATÓRIOS
# ==============================================================================
def relatorio_corpo_clinico(conn):
    """Lista médicos, CRMs e especialidades"""
    sql = """
    SELECT 
        P."NOME" AS "Nome do Médico", 
        M."CRM", 
        E."NOME_ESPECIALIDADE" AS "Especialidade"
    FROM "MEDICO" M
    JOIN "PESSOA" P ON M."CPF" = P."CPF"
    JOIN "MEDICO_ESPECIALIDADE" ME ON M."CRM" = ME."CRM"
    JOIN "ESPECIALIDADE" E ON ME."ID_ESPECIALIDADE" = E."ID_ESPECIALIDADE"
    ORDER BY P."NOME";
    """
    df = pd.read_sql_query(sql, conn)
    return df, "📋 CORPO CLÍNICO - Médicos e Especialidades"

def relatorio_procedimentos(conn):
    """Relatório financeiro de procedimentos"""
    sql = """
    SELECT 
        PROC."DATE" AS "Data",
        PROC."TIPO_PROCEDIMENTO" AS "Procedimento",
        PES_PAC."NOME" AS "Paciente",
        PAG."NOME_PAGADOR" AS "Quem Pagou",
        PROC."CUSTO" AS "Valor"
    FROM "PROCEDIMENTO" PROC
    JOIN "PACIENTE" PAC ON PROC."CPF_PACIENTE" = PAC."CPF_PACIENTE"
    JOIN "PESSOA" PES_PAC ON PAC."CPF_PACIENTE" = PES_PAC."CPF"
    JOIN "PAGADOR" PAG ON PROC."ID_PAGADOR" = PAG."ID_PAGADOR"
    ORDER BY PROC."DATE" DESC;
    """
    df = pd.read_sql_query(sql, conn)
    if not df.empty:
        df["Valor"] = df["Valor"].apply(lambda x: f"R$ {x:,.2f}")
    return df, "💰 PROCEDIMENTOS REALIZADOS"

def relatorio_rh(conn):
    """Estatísticas de RH por departamento"""
    sql = """
    SELECT 
        D."NOME_DEPARTAMENTO" AS "Departamento",
        COUNT(F."CPF") AS "Qtd Funcionários",
        ROUND(AVG(F."SALARIO"), 2) AS "Média Salarial",
        ROUND(MAX(F."SALARIO"), 2) AS "Maior Salário",
        ROUND(MIN(F."SALARIO"), 2) AS "Menor Salário"
    FROM "FUNCIONARIO" F
    JOIN "DEPARTAMENTO" D ON F."ID_DEPARTAMENTO" = D."ID_DEPARTAMENTO"
    GROUP BY D."NOME_DEPARTAMENTO"
    ORDER BY "Média Salarial" DESC;
    """
    df = pd.read_sql_query(sql, conn)
    if not df.empty:
        df["Média Salarial"] = df["Média Salarial"].apply(lambda x: f"R$ {x:,.2f}")
        df["Maior Salário"] = df["Maior Salário"].apply(lambda x: f"R$ {x:,.2f}")
        df["Menor Salário"] = df["Menor Salário"].apply(lambda x: f"R$ {x:,.2f}")
    return df, "📊 ANÁLISE RH - Estatísticas por Departamento"

def relatorio_receita_total(conn):
    """Receita total e estatísticas financeiras"""
    sql = """
    SELECT 
        COUNT(*) AS "Total Procedimentos",
        ROUND(SUM(PROC."CUSTO"), 2) AS "Receita Total",
        ROUND(AVG(PROC."CUSTO"), 2) AS "Ticket Médio",
        ROUND(MAX(PROC."CUSTO"), 2) AS "Procedimento Mais Caro",
        ROUND(MIN(PROC."CUSTO"), 2) AS "Procedimento Mais Barato"
    FROM "PROCEDIMENTO" PROC;
    """
    df = pd.read_sql_query(sql, conn)
    if not df.empty:
        df["Receita Total"] = df["Receita Total"].apply(lambda x: f"R$ {x:,.2f}")
        df["Ticket Médio"] = df["Ticket Médio"].apply(lambda x: f"R$ {x:,.2f}")
        df["Procedimento Mais Caro"] = df["Procedimento Mais Caro"].apply(lambda x: f"R$ {x:,.2f}")
        df["Procedimento Mais Barato"] = df["Procedimento Mais Barato"].apply(lambda x: f"R$ {x:,.2f}")
    return df, "💵 RECEITA TOTAL - Estatísticas Financeiras"

def relatorio_procedimentos_por_tipo(conn):
    """Procedimentos agrupados por tipo"""
    sql = """
    SELECT 
        PROC."TIPO_PROCEDIMENTO" AS "Tipo de Procedimento",
        COUNT(*) AS "Quantidade",
        ROUND(SUM(PROC."CUSTO"), 2) AS "Receita Total",
        ROUND(AVG(PROC."CUSTO"), 2) AS "Valor Médio"
    FROM "PROCEDIMENTO" PROC
    GROUP BY PROC."TIPO_PROCEDIMENTO"
    ORDER BY "Receita Total" DESC;
    """
    df = pd.read_sql_query(sql, conn)
    if not df.empty:
        df["Receita Total"] = df["Receita Total"].apply(lambda x: f"R$ {x:,.2f}")
        df["Valor Médio"] = df["Valor Médio"].apply(lambda x: f"R$ {x:,.2f}")
    return df, "📈 PROCEDIMENTOS POR TIPO"

def relatorio_pacientes(conn):
    """Lista de pacientes cadastrados"""
    sql = """
    SELECT 
        P."NOME" AS "Nome",
        P."CPF",
        P."DATA_NASCIMENTO" AS "Data de Nascimento",
        P."TELEFONE",
        P."EMAIL"
    FROM "PACIENTE" PAC
    JOIN "PESSOA" P ON PAC."CPF_PACIENTE" = P."CPF"
    ORDER BY P."NOME";
    """
    df = pd.read_sql_query(sql, conn)
    return df, "👥 PACIENTES CADASTRADOS"

def relatorio_funcionarios_completo(conn):
    """Lista completa de funcionários"""
    sql = """
    SELECT 
        P."NOME" AS "Nome",
        F."CPF",
        D."NOME_DEPARTAMENTO" AS "Departamento",
        F."SALARIO" AS "Salário",
        F."DATA_ADMISSAO" AS "Data de Admissão"
    FROM "FUNCIONARIO" F
    JOIN "PESSOA" P ON F."CPF" = P."CPF"
    JOIN "DEPARTAMENTO" D ON F."ID_DEPARTAMENTO" = D."ID_DEPARTAMENTO"
    ORDER BY F."SALARIO" DESC;
    """
    df = pd.read_sql_query(sql, conn)
    if not df.empty:
        df["Salário"] = df["Salário"].apply(lambda x: f"R$ {x:,.2f}")
    return df, "👔 FUNCIONÁRIOS - Lista Completa"

def relatorio_top_medicos(conn):
    """Top médicos por número de procedimentos"""
    sql = """
    SELECT 
        P."NOME" AS "Nome do Médico",
        M."CRM",
        COUNT(PROC."ID_PROCEDIMENTO") AS "Total Procedimentos",
        ROUND(SUM(PROC."CUSTO"), 2) AS "Receita Gerada"
    FROM "MEDICO" M
    JOIN "PESSOA" P ON M."CPF" = P."CPF"
    LEFT JOIN "PROCEDIMENTO" PROC ON M."CRM" = PROC."CRM"
    GROUP BY P."NOME", M."CRM"
    ORDER BY "Total Procedimentos" DESC, "Receita Gerada" DESC;
    """
    df = pd.read_sql_query(sql, conn)
    if not df.empty:
        df["Receita Gerada"] = df["Receita Gerada"].apply(lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "R$ 0,00")
    return df, "🏆 TOP MÉDICOS - Por Performance"

def relatorio_departamentos(conn):
    """Informações sobre departamentos"""
    sql = """
    SELECT 
        D."NOME_DEPARTAMENTO" AS "Departamento",
        COUNT(DISTINCT F."CPF") AS "Funcionários",
        COUNT(DISTINCT M."CRM") AS "Médicos",
        COUNT(DISTINCT PROC."ID_PROCEDIMENTO") AS "Procedimentos Realizados"
    FROM "DEPARTAMENTO" D
    LEFT JOIN "FUNCIONARIO" F ON D."ID_DEPARTAMENTO" = F."ID_DEPARTAMENTO"
    LEFT JOIN "MEDICO" M ON F."CPF" = M."CPF"
    LEFT JOIN "PROCEDIMENTO" PROC ON M."CRM" = PROC."CRM"
    GROUP BY D."NOME_DEPARTAMENTO"
    ORDER BY D."NOME_DEPARTAMENTO";
    """
    df = pd.read_sql_query(sql, conn)
    return df, "🏥 DEPARTAMENTOS - Visão Geral"

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def exibir_relatorio(df, titulo):
    """Exibe um relatório formatado"""
    print("\n" + "="*70)
    print(f"  {titulo}")
    print("="*70)
    if df.empty:
        print("⚠️  Nenhum dado encontrado.")
    else:
        print(df.to_string(index=False))
    print("="*70 + "\n")

def exportar_csv(df, nome_arquivo):
    """Exporta DataFrame para CSV"""
    try:
        if not os.path.exists("relatorios"):
            os.makedirs("relatorios")
        caminho = f"relatorios/{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(caminho, index=False, encoding='utf-8-sig')
        print(f"✅ Relatório exportado: {caminho}")
        return True
    except Exception as e:
        print(f"❌ Erro ao exportar: {e}")
        return False

def exportar_excel(df, nome_arquivo):
    """Exporta DataFrame para Excel"""
    try:
        if not os.path.exists("relatorios"):
            os.makedirs("relatorios")
        caminho = f"relatorios/{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(caminho, index=False, engine='openpyxl')
        print(f"✅ Relatório exportado: {caminho}")
        return True
    except Exception as e:
        print(f"❌ Erro ao exportar (pode precisar instalar openpyxl): {e}")
        return False

# ==============================================================================
# MENU PRINCIPAL
# ==============================================================================
def exibir_menu():
    """Exibe o menu de opções"""
    print("\n" + "="*70)
    print("  🏥 SISTEMA DE RELATÓRIOS HOSPITALARES")
    print("="*70)
    print("  1  - Corpo Clínico (Médicos e Especialidades)")
    print("  2  - Procedimentos Realizados")
    print("  3  - Análise RH (Estatísticas por Departamento)")
    print("  4  - Receita Total e Estatísticas Financeiras")
    print("  5  - Procedimentos por Tipo")
    print("  6  - Pacientes Cadastrados")
    print("  7  - Funcionários (Lista Completa)")
    print("  8  - Top Médicos (Por Performance)")
    print("  9  - Departamentos (Visão Geral)")
    print("  10 - TODOS OS RELATÓRIOS")
    print("  0  - Sair")
    print("="*70)

def processar_opcao(conn, opcao):
    """Processa a opção selecionada"""
    relatorios = {
        '1': relatorio_corpo_clinico,
        '2': relatorio_procedimentos,
        '3': relatorio_rh,
        '4': relatorio_receita_total,
        '5': relatorio_procedimentos_por_tipo,
        '6': relatorio_pacientes,
        '7': relatorio_funcionarios_completo,
        '8': relatorio_top_medicos,
        '9': relatorio_departamentos,
    }
    
    if opcao == '10':
        # Executar todos os relatórios
        for key, func in relatorios.items():
            try:
                df, titulo = func(conn)
                exibir_relatorio(df, titulo)
            except Exception as e:
                print(f"❌ Erro ao gerar relatório: {e}\n")
    elif opcao in relatorios:
        try:
            df, titulo = relatorios[opcao](conn)
            exibir_relatorio(df, titulo)
            
            # Perguntar se deseja exportar
            exportar = input("💾 Deseja exportar este relatório? (s/n): ").lower()
            if exportar == 's':
                formato = input("   Formato (csv/excel): ").lower()
                nome_base = titulo.lower().replace(' ', '_').replace('-', '_')
                if formato == 'excel':
                    exportar_excel(df, nome_base)
                else:
                    exportar_csv(df, nome_base)
        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {e}\n")
    else:
        print("⚠️  Opção inválida!")

def main():
    """Função principal"""
    print("🔌 Conectando ao Banco de Dados Hospitalar...")
    conn = conectar_banco()
    
    if not conn:
        print("❌ Não foi possível conectar ao banco de dados.")
        return
    
    print("✅ Conexão estabelecida com sucesso!\n")
    
    try:
        while True:
            exibir_menu()
            opcao = input("👉 Escolha uma opção: ").strip()
            
            if opcao == '0':
                print("\n👋 Encerrando sistema...")
                break
            
            processar_opcao(conn, opcao)
            
            if opcao != '0':
                input("\n⏎ Pressione ENTER para continuar...")
    
    except KeyboardInterrupt:
        print("\n\n👋 Sistema interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
    finally:
        if conn:
            conn.close()
            print("🔌 Conexão encerrada.")

if __name__ == "__main__":
    main()