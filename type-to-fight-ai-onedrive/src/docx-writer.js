'use strict';

const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, HeadingLevel } = require('docx');

// Rebuilds the DOCX from the full accumulated text each time.
// Paragraphs are split on newlines; blank lines become empty paragraphs (spacing).
async function writeDocx(filePath, text) {
  const lines = text.split('\n');

  const paragraphs = lines.map(line => {
    const trimmed = line.trim();
    if (!trimmed) {
      return new Paragraph({});
    }
    return new Paragraph({
      children: [new TextRun({ text: trimmed, size: 24, font: 'Calibri' })],
      spacing: { after: 120 },
    });
  });

  const doc = new Document({
    sections: [{
      properties: {},
      children: paragraphs,
    }],
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(filePath, buffer);
}

module.exports = { writeDocx };
