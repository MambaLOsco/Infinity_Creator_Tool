import express from "express";
import cors from "cors";
import { router } from "./routes";

const app = express();
const port = process.env.PORT ? Number(process.env.PORT) : 3001;

app.use(cors());
app.use(express.json({ limit: "2mb" }));
app.use(express.urlencoded({ extended: true }));

app.get("/api/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.use(router);

app.listen(port, () => {
  console.log(`Infinity Creator Tool server listening on ${port}`);
});
