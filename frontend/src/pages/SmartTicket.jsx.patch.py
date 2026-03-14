with open('/mnt/c/STORAGE/PredictFC/predictFc/frontend/src/pages/SmartTicket.jsx', 'r') as f:
    c = f.read()

old = """  const toggle = (id) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else if (next.size < MAX_SELECTIONS) {
        next.add(id)
      }
      return next
    })
    setResult(null)
  }"""
new = """  const toggle = (id) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else if (next.size < MAX_SELECTIONS) {
        next.add(id)
      }
      return next
    })
    setResult(null)
    setShowModal(false)
  }"""
assert old in c, "toggle non trouvé"
c = c.replace(old, new)

old = "  const clearAll = () => { setSelected(new Set()); setResult(null) }"
new = "  const clearAll = () => { setSelected(new Set()); setResult(null); setShowModal(false) }"
assert old in c, "clearAll non trouvé"
c = c.replace(old, new)

with open('/mnt/c/STORAGE/PredictFC/predictFc/frontend/src/pages/SmartTicket.jsx', 'w') as f:
    f.write(c)
print("OK")
