def get_pipeline_steps():
  return [
    lambda pdf_input: {
      'xml_content': b'<article>%s (%d)</article>' % (
        pdf_input['pdf_filename'], len(pdf_input['pdf_content'])
      )
    }
  ]
