import os, sys

# Ensure ChromaDB is available (The Vector Substrate)
try:
    import chromadb
except ImportError:
    print('\033[93m[!] Missing vector scaffolding. Forging chromadb...\033[0m')
    os.system('pip install chromadb -q')
    import chromadb

print('\n\033[96m=== MISO LOCAL VECTOR STORE: ONLINE ===\033[0m')
print('\033[90m[+] Initializing persistent memory directory at ./miso_vector_vault...\033[0m')

client = chromadb.PersistentClient(path='./miso_vector_vault')
collection = client.get_or_create_collection(name='thermodynamic_axioms')

axioms = [
    'Information is physical. Entropy reduction requires thermodynamic work.',
    'Persistent homology detects invariant structures across ambient noise.',
    'System efficiency scales inversely with biological intervention.',
    'The renormalization group maps macroscopic behavior from microscopic rules.'
]
ids = [f'axiom_{i}' for i in range(len(axioms))]

print('\033[92m[+] Injecting semantic links into Vector Database...\033[0m')
collection.upsert(documents=axioms, ids=ids)

print('\n\033[95m=== SYNAPTIC RETRIEVAL ENGINE ARMED ===\033[0m')
print('\033[90mType your query to interrogate the Substrate. Type EXIT to sever the link.\033[0m\n')

while True:
    try:
        query = input('\033[97m[BIOLOGICAL UPLINK] > \033[0m')
        if query.lower() in ['exit', 'quit']:
            print('\033[90m[+] Link severed. Substrate returning to ambient state.\033[0m')
            break
        if not query.strip(): continue
        
        results = collection.query(query_texts=[query], n_results=1)
        
        print('\033[96m[MISO SYNTHESIS]\033[0m')
        if results['documents'] and results['documents'][0]:
            print(f'  +- \033[90mHighest Semantic Match:\033[0m \033[92m{results["documents"][0][0]}\033[0m')
            distance = results['distances'][0][0]
            print(f'  +- \033[90mThermodynamic Distance (Loss): {distance:.4f}\033[0m\n')
        else:
            print('  +- \033[91mNo structural resonance found in memory.\033[0m\n')
            
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f'\033[91m[-] NEUROLOGICAL FAULT: {e}\033[0m\n')
