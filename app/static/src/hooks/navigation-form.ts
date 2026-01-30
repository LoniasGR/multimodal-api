import { createFormHook } from '@tanstack/react-form'

import {
  PickOne,
  Select,
  SubmitButton,
  TextField,
} from '../components/forms/forms-components'
import { fieldContext, formContext } from './form-context'

export const { useAppForm } = createFormHook({
  fieldComponents: {
    TextField,
    Select,
    PickOne
  },
  formComponents: {
    SubmitButton,
  },
  fieldContext,
  formContext,
})
