import express from "express";
import { getStock, setStock } from "./store";

const app = express();
app.use(express.json());

app.get("/healthz", (_req, res) => res.send("ok"));

app.get("/stock/:sku", async (req, res) => {
  const qty = await getStock(req.params.sku);
  res.json({ sku: req.params.sku, qty });
});

app.put("/stock/:sku", async (req, res) => {
  try {
    await setStock(req.params.sku, req.body.qty);
    res.status(204).end();
  } catch (e) {
    console.log("error", e);
    res.status(500).end();
  }
});

app.listen(3000);
