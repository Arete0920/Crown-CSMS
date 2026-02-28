import { Table, TableBody, TableCell, TableHead, TableRow } from "@mui/material";

export default function BoardSimpleTable({ columns, rows }) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          {columns.map((c) => (
            <TableCell
              key={c.key}
              align={c.align || "left"}
              sx={{ fontWeight: 600 }}
            >
              {c.label}
            </TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map((r, idx) => (
          <TableRow key={idx} hover>
            {columns.map((c) => (
              <TableCell key={c.key} align={c.align || "left"}>
                {typeof c.render === "function" ? c.render(r) : r[c.key]}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
