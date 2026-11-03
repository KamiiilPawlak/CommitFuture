import { Route, Routes } from "react-router-dom"
import { Header } from "@/components/Header"
import { Main } from "@/components/Main"
import { HistoryPage } from "@/components/HistoryPage"

function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <Routes>
        <Route path="/" element={<Main />} />
        <Route path="/historia" element={<HistoryPage />} />
      </Routes>
    </div>
  )
}

export default App
